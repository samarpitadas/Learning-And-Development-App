from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import CustomUser, Course, Module, CourseAssignment, ModuleProgress, CourseFeedback
from .forms import RegistrationForm, LoginForm, CourseForm, ModuleFormSet, CourseFeedbackForm
import json
from .models import CustomUser, Course, Module, CourseAssignment, ModuleProgress, CourseFeedback, Notification


# Authentication Views
def home(request):
    return render(request, 'home.html')

def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'manager':
                return redirect('manager_dashboard')
            else:
                return redirect('employee_dashboard')
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def user_login(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(username=username, password=password)
            if user:
                login(request, user)
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'manager':
                    return redirect('manager_dashboard')
                else:
                    return redirect('employee_dashboard')
    else:
        form = LoginForm()
    return render(request, 'login.html', {'form': form})

def user_logout(request):
    logout(request)
    return redirect('home')

# Dashboard Views
@login_required
def admin_dashboard(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    courses = Course.objects.all()
    assignments = CourseAssignment.objects.all().order_by('-assigned_date').select_related('employee', 'course')
    feedbacks = CourseFeedback.objects.all().select_related('course', 'employee')
    requests = Request.objects.all()
    recent_credentials = EmployeeCredential.objects.all().order_by('-created_at')[:5]

    # Rating statistics for pie chart
    rating_counts = {i: 0 for i in range(1, 6)}
    for feedback in feedbacks:
        rating_counts[feedback.rating] += 1
    
    feedback_chart_data = {
        'labels': ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
        'values': list(rating_counts.values()),
        'colors': ['#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', '#9966FF']
    }

    # Progress tracking
    progress_data = []
    chart_data = {'labels': [], 'progress_values': []}
    
    all_modules = Module.objects.filter(course__in=[a.course for a in assignments])
    module_progress = ModuleProgress.objects.filter(
        employee__in=[a.employee for a in assignments],
        module__in=all_modules,
        completed=True
    ).select_related('module', 'employee')
    
    progress_lookup = {}
    for mp in module_progress:
        key = (mp.employee_id, mp.module.course_id)
        if key not in progress_lookup:
            progress_lookup[key] = {'completed': 0, 'last_activity': None}
        progress_lookup[key]['completed'] += 1
        if mp.completion_date:
            current_last = progress_lookup[key]['last_activity']
            if not current_last or mp.completion_date > current_last:
                progress_lookup[key]['last_activity'] = mp.completion_date
    
    unique_employees = set()
    
    for assignment in assignments:
        total_modules = assignment.course.modules.count()
        key = (assignment.employee.id, assignment.course.id)
        progress_info = progress_lookup.get(key, {'completed': 0, 'last_activity': None})
        
        completed_modules = progress_info['completed']
        progress = (completed_modules / total_modules * 100) if total_modules > 0 else 0
        
        chart_data['labels'].append(f"{assignment.employee.email} - {assignment.course.name}")
        chart_data['progress_values'].append(round(progress, 1))
        unique_employees.add(assignment.employee)
        
        progress_data.append({
            'employee': assignment.employee,
            'course': assignment.course,
            'progress': progress,
            'completed_modules': completed_modules,
            'total_modules': total_modules,
            'start_date': assignment.assigned_date,
            'last_activity': progress_info['last_activity'],
            'status': 'Completed' if progress == 100 else 'In Progress' if progress > 0 else 'Not Started'
        })

    # Dashboard statistics
    total_employees = len(unique_employees)
    total_courses = courses.count()
    total_assignments = len(assignments)
    active_employees = EmployeeCredential.objects.filter(is_active=True).count()
    
    context = {
        'courses': courses,
        'progress_data': progress_data,
        'feedbacks': feedbacks,
        'total_employees': total_employees,
        'total_courses': total_courses,
        'total_assignments': total_assignments,
        'active_employees': active_employees,
        'chart_data': {
            'labels': json.dumps(chart_data['labels']),
            'progress_values': json.dumps(chart_data['progress_values'])
        },
        'feedback_chart_data': json.dumps(feedback_chart_data),
        'requests': requests,
        'recent_credentials': recent_credentials
    }
    
    return render(request, 'admin_dashboard.html', context)


from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Request
from .forms import RequestForm
@login_required
def manager_dashboard(request):
    requests_list = Request.objects.filter(created_by=request.user)
    data = []
    for req in requests_list:
        data.append({
            'id': req.id,
            'name': req.name,
            'description': req.description,
            'concept': req.concept,
            'duration': req.duration,
            'deadline': req.deadline,
            'status': req.status,
            'created_at': req.created_at,
        })
    return render(request, 'manager_dashboard.html', {'requests': data})
@login_required
def view_request(request, pk):
    request_obj = Request.objects.get(pk=pk)
    return render(request, 'view_request.html', {'request': request_obj})
@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.created_by = request.user
            request_obj.save()
            return redirect('manager_dashboard')
    else:
        form = RequestForm()
    return render(request, 'create_request.html', {'form': form})

@login_required
def employee_dashboard(request):
    if request.user.role != 'employee':
        return redirect('home')
    
    assignments = CourseAssignment.objects.filter(employee=request.user).select_related('course')
    courses_data = []
    
    unread_notifications = Notification.objects.filter(
        recipient=request.user,
        is_read=False
    ).count()
    
    for assignment in assignments:
        modules = assignment.course.modules.all().prefetch_related('moduleprogress_set')
        module_progress = []
        completed_count = 0
        
        feedback = CourseFeedback.objects.filter(
            course=assignment.course,
            employee=request.user
        ).first()
        
        last_activity = ModuleProgress.objects.filter(
            module__course=assignment.course,
            employee=request.user,
            completed=True
        ).order_by('-completion_date').first()
        
        for module in modules:
            progress = ModuleProgress.objects.filter(
                module=module,
                employee=request.user
            ).first()
            
            if progress and progress.completed:
                completed_count += 1
            
            module_progress.append({
                'module': module,
                'completed': progress.completed if progress else False,
                'completion_date': progress.completion_date if progress else None
            })
        
        progress_percentage = (completed_count / len(modules) * 100) if modules else 0
        
        today = timezone.now().date()
        days_until_deadline = (assignment.course.deadline - today).days
        deadline_status = 'On Track'
        if days_until_deadline < 0:
            deadline_status = 'Overdue'
        elif days_until_deadline <= 7:
            deadline_status = 'Due Soon'
        
        courses_data.append({
            'course': assignment.course,
            'modules': module_progress,
            'progress': progress_percentage,
            'has_feedback': bool(feedback),
            'feedback': feedback,
            'assigned_date': assignment.assigned_date,
            'deadline': assignment.course.deadline,
            'deadline_status': deadline_status,
            'days_remaining': max(days_until_deadline, 0),
            'last_activity': last_activity.completion_date if last_activity else None
        })
    
    courses_data.sort(key=lambda x: x['deadline'])
    
    context = {
        'courses_data': courses_data,
        'total_courses': len(courses_data),
        'completed_courses': sum(1 for course in courses_data if course['progress'] == 100),
        'in_progress_courses': sum(1 for course in courses_data if 0 < course['progress'] < 100),
        'not_started_courses': sum(1 for course in courses_data if course['progress'] == 0),
        'unread_notifications': unread_notifications,
        'overdue_courses': sum(1 for course in courses_data if course['deadline_status'] == 'Overdue')
    }
    
    return render(request, 'employee_dashboard.html', context)



# Course Management Views
@login_required
def create_course(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        course_form = CourseForm(request.POST)
        module_formset = ModuleFormSet(request.POST)
        
        if course_form.is_valid() and module_formset.is_valid():
            course = course_form.save()
            modules = module_formset.save(commit=False)
            for module in modules:
                module.course = course
                module.save()

            employees = CustomUser.objects.filter(role='employee')
            for employee in employees:
                Notification.objects.create(
                    recipient=employee,
                    message=f"New course '{course.name}' has been created",
                    course=course
                )   
            return redirect('admin_dashboard')
    else:
        course_form = CourseForm()
        module_formset = ModuleFormSet(queryset=Module.objects.none())
    
    return render(request, 'create_course.html', {
        'course_form': course_form,
        'module_formset': module_formset
    })

@login_required
def edit_course(request, course_id):
    if request.user.role != 'admin':
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        course_form = CourseForm(request.POST, instance=course)
        module_formset = ModuleFormSet(request.POST, queryset=Module.objects.filter(course=course))
        
        if course_form.is_valid() and module_formset.is_valid():
            course_form.save()
            modules = module_formset.save(commit=False)
            for module in modules:
                module.course = course
                module.save()
            return redirect('admin_dashboard')
    else:
        course_form = CourseForm(instance=course)
        module_formset = ModuleFormSet(queryset=Module.objects.filter(course=course))
    
    return render(request, 'edit_course.html', {
        'course_form': course_form,
        'module_formset': module_formset
    })

@login_required
def delete_course(request, course_id):
    if request.user.role != 'admin':
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    course.delete()
    messages.success(request, 'Course deleted successfully')
    return redirect('admin_dashboard')

# Course Assignment and Progress Views
@login_required
def assign_course(request, course_id):
    if request.user.role != 'admin':
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        employee_email = request.POST.get('employee_email')
        try:
            employee = CustomUser.objects.get(email=employee_email, role='employee')
            CourseAssignment.objects.create(course=course, employee=employee)
            messages.success(request, f'Course assigned to {employee.email} successfully')
        except CustomUser.DoesNotExist:
            messages.error(request, 'Employee not found')
        except CustomUser.MultipleObjectsReturned:
            messages.error(request, 'Multiple employees found with this email. Please contact system administrator.')
    
    return redirect('admin_dashboard')

@login_required
def mark_module_complete(request, module_id):
    if request.user.role != 'employee':
        return redirect('home')
    
    module = get_object_or_404(Module, id=module_id)
    progress, created = ModuleProgress.objects.get_or_create(
        module=module,
        employee=request.user
    )
    
    progress.completed = True
    progress.completion_date = timezone.now()
    progress.save()
    
    return redirect('employee_dashboard')

@login_required
def submit_feedback(request, course_id):
    if request.user.role != 'employee':
        return redirect('home')
    
    course = get_object_or_404(Course, id=course_id)

    existing_feedback = CourseFeedback.objects.filter(
        course=course,
        employee=request.user
    ).exists()
    
    if existing_feedback:
        messages.warning(request, 'You have already submitted feedback for this course.')
        return redirect('employee_dashboard')
    
    if request.method == 'POST':
        form = CourseFeedbackForm(request.POST)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.course = course
            feedback.employee = request.user
            feedback.save()
            messages.success(request, 'Feedback submitted successfully!')
            return redirect('employee_dashboard')
    else:
        form = CourseFeedbackForm()
    
    return render(request, 'submit_feedback.html', {
        'form': form,
        'course': course
    })

@login_required
def create_request(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.created_by = request.user
            request_obj.save()
            return redirect('manager_dashboard')
    else:
        form = RequestForm()
    return render(request, 'create_request.html', {'form': form})

@login_required
def update_request_status(request, pk):
    request_obj = Request.objects.get(pk=pk)
    if request.method == 'POST':
        status = request.POST.get('status')
        request_obj.status = status
        request_obj.save()
        return redirect('admin_dashboard')
    return render(request, 'update_request_status.html', {'request_obj': request_obj})

@login_required
def view_request(request, pk):
    req = Request.objects.get(pk=pk)
    return render(request, 'view_request.html', {'request': req})

@login_required
def notifications(request):
    notifications = Notification.objects.filter(recipient=request.user, is_read=False)
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required
def mark_notification_read(request, notification_id):
    notification = get_object_or_404(Notification, id=notification_id, recipient=request.user)
    notification.is_read = True
    notification.save()
    return redirect('notifications')


import random
import string
from django.contrib.auth.hashers import make_password

def generate_random_password():
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for i in range(10))

def generate_unique_username(base_username):
    username = base_username
    counter = 1
    while CustomUser.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    return username

@login_required
def generate_employee_credentials(request):
    if request.user.role != 'admin':
        return redirect('home')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        base_username = email.split('@')[0]
        username = generate_unique_username(base_username)
        password = generate_random_password()
        
        user = CustomUser.objects.create(
            username=username,
            email=email,
            password=make_password(password),
            role='employee'
        )
        
        EmployeeCredential.objects.create(
            employee=user,
            username=username,
            password=password
        )
        
        messages.success(request, f'Credentials generated for {email}. Username: {username}, Password: {password}')
        
        Notification.objects.create(
            recipient=user,
            message=f"Welcome! Your account has been created.",
        )
        
        return redirect('admin_dashboard')
    
    return render(request, 'generate_credentials.html')
from .models import CustomUser, Course, Module, CourseAssignment, ModuleProgress, CourseFeedback, Notification, EmployeeCredential
