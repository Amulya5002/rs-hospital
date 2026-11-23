
from .models import Department

def hospital_departments(request):
    return {
        'nav_departments': Department.objects.order_by(
            'department_name'
        )
    }
