from django.contrib import admin
from .models import CustomUser, Course, Module, CourseAssignment, ModuleProgress ,CourseFeedback, Request, Notification, EmployeeCredential
admin.site.register(CustomUser)
admin.site.register(Course)
admin.site.register(Module)
admin.site.register(CourseAssignment)
admin.site.register(ModuleProgress)
admin.site.register(CourseFeedback)
admin.site.register(Request)
admin.site.register(Notification)
admin.site.register(EmployeeCredential)