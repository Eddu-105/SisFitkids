import csv
import json
from datetime import date
from io import StringIO

from django.contrib.auth import authenticate, get_user_model, login, logout, update_session_auth_hash
from django.db.models import Count, Sum
from django.http import HttpResponse, JsonResponse
from django.utils.dateparse import parse_time
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import (
    Announcement,
    AppSetting,
    AttendanceRecord,
    AttendanceSession,
    ClassGroup,
    ParentProfile,
    Payment,
    ProgressEvaluation,
    Student,
)


def health(request):
    return JsonResponse({'status': 'ok', 'app': 'SIS Fit Kids'})


def dashboard_summary(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    User = get_user_model()
    return JsonResponse({
        'students': Student.objects.count(),
        'parents': ParentProfile.objects.count(),
        'teachers': User.objects.filter(role=User.Role.TEACHER).count(),
        'pending_payments': Payment.objects.filter(status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]).count(),
        'weekly_classes': ClassGroup.objects.filter(is_active=True).count(),
        'today_sessions': AttendanceSession.objects.filter(date=date.today()).count(),
        'month_income': str(Payment.objects.filter(status=Payment.Status.PAID, paid_date__month=date.today().month).aggregate(total=Sum('amount'))['total'] or 0),
        'announcements': Announcement.objects.filter(is_active=True).count(),
    })


def parent_to_dict(parent):
    user = parent.user
    return {
        'id': parent.id,
        'user_id': user.id,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'username': user.username,
        'email': user.email,
        'dni': parent.dni,
        'phone': parent.phone,
        'address': parent.address,
        'emergency_phone': parent.emergency_phone,
        'children_count': parent.children.count(),
    }


def student_to_dict(student):
    return {
        'id': student.id,
        'first_name': student.first_name,
        'last_name': student.last_name,
        'full_name': str(student),
        'birth_date': student.birth_date.isoformat(),
        'status': student.status,
        'status_label': student.get_status_display(),
        'weight_kg': str(student.weight_kg) if student.weight_kg is not None else '',
        'height_cm': str(student.height_cm) if student.height_cm is not None else '',
        'medical_notes': student.medical_notes,
        'teacher_notes': student.teacher_notes,
        'parent': parent_to_dict(student.parent),
        'class_group': class_group_to_dict(student.class_group) if student.class_group else None,
    }


def class_group_days(class_group):
    days = class_group.days_of_week or [class_group.day_of_week]
    return [int(day) for day in days if day]


def day_label(day):
    return ClassGroup.Day(int(day)).label


def class_group_to_dict(class_group):
    days = class_group_days(class_group)
    day_labels = [day_label(day) for day in days]
    return {
        'id': class_group.id,
        'name': class_group.name,
        'day_of_week': class_group.day_of_week,
        'day_label': day_labels[0] if day_labels else class_group.get_day_of_week_display(),
        'days_of_week': days,
        'day_labels': day_labels,
        'start_time': class_group.start_time.strftime('%H:%M'),
        'end_time': class_group.end_time.strftime('%H:%M'),
        'capacity': class_group.capacity,
        'age_range': class_group.age_range,
        'color': class_group.color,
        'is_active': class_group.is_active,
        'students_count': class_group.students.count(),
    }


def request_group_days(data, current_group=None):
    raw_days = data.get('days_of_week')
    if raw_days is None:
        raw_days = [data.get('day_of_week')] if data.get('day_of_week') else None
    if raw_days is None and current_group:
        raw_days = class_group_days(current_group)
    if raw_days is None:
        return []
    if not isinstance(raw_days, list):
        raw_days = [raw_days]
    try:
        days = sorted({int(day) for day in raw_days if str(day).strip()})
    except (TypeError, ValueError):
        return []
    return [day for day in days if day in ClassGroup.Day.values]


def request_group_time(data, field, current_group=None):
    value = data.get(field)
    if value in [None, ''] and current_group:
        return getattr(current_group, field)
    parsed = parse_time(str(value or ''))
    return parsed


def find_group_collision(days, start_time, end_time, exclude_id=None):
    groups = ClassGroup.objects.filter(is_active=True)
    if exclude_id:
        groups = groups.exclude(id=exclude_id)
    day_set = set(days)
    for group in groups:
        if day_set.intersection(class_group_days(group)) and start_time < group.end_time and end_time > group.start_time:
            return group
    return None


def payment_to_dict(payment):
    return {
        'id': payment.id,
        'student': student_to_dict(payment.student),
        'concept': payment.concept,
        'amount': str(payment.amount),
        'due_date': payment.due_date.isoformat(),
        'paid_date': payment.paid_date.isoformat() if payment.paid_date else '',
        'status': payment.status,
        'status_label': payment.get_status_display(),
        'notes': payment.notes,
    }


def attendance_record_to_dict(record):
    return {
        'id': record.id,
        'student': student_to_dict(record.student),
        'status': record.status,
        'status_label': record.get_status_display(),
        'notes': record.notes,
    }


def attendance_session_to_dict(session):
    return {
        'id': session.id,
        'class_group': class_group_to_dict(session.class_group),
        'date': session.date.isoformat(),
        'notes': session.notes,
        'records': [attendance_record_to_dict(record) for record in session.records.all()],
    }


def progress_to_dict(evaluation):
    return {
        'id': evaluation.id,
        'student': student_to_dict(evaluation.student),
        'date': evaluation.date.isoformat(),
        'weight_kg': str(evaluation.weight_kg) if evaluation.weight_kg is not None else '',
        'height_cm': str(evaluation.height_cm) if evaluation.height_cm is not None else '',
        'strength': evaluation.strength,
        'endurance': evaluation.endurance,
        'coordination': evaluation.coordination,
        'flexibility': evaluation.flexibility,
        'notes': evaluation.notes,
    }


def announcement_to_dict(announcement):
    return {
        'id': announcement.id,
        'title': announcement.title,
        'body': announcement.body,
        'audience': announcement.audience,
        'audience_label': announcement.get_audience_display(),
        'parent': parent_to_dict(announcement.parent) if announcement.parent else None,
        'is_active': announcement.is_active,
        'created_at': announcement.created_at.isoformat(),
    }


def setting_to_dict(setting):
    return {
        'id': setting.id,
        'academy_name': setting.academy_name,
        'teacher_name': setting.teacher_name,
        'phone': setting.phone,
        'address': setting.address,
        'default_monthly_fee': str(setting.default_monthly_fee),
    }


def get_settings():
    setting, _ = AppSetting.objects.get_or_create(id=1)
    return setting


def request_data(request):
    try:
        return json.loads(request.body.decode('utf-8') or '{}')
    except json.JSONDecodeError:
        return None


def json_error(message, status=400):
    return JsonResponse({'error': message}, status=status)


def user_to_dict(user):
    return {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'full_name': user.get_full_name() or user.username,
        'email': user.email,
        'role': user.role,
    }


def require_authenticated(request):
    if not request.user.is_authenticated:
        return json_error('Debes iniciar sesion.', status=401)
    return None


def require_teacher(request):
    auth_error = require_authenticated(request)
    if auth_error:
        return auth_error
    if not request.user.is_teacher:
        return json_error('No tienes permiso para esta accion.', status=403)
    return None


@csrf_exempt
@require_http_methods(['POST'])
def login_view(request):
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    user = authenticate(request, username=username, password=password)
    if user is None:
        return json_error('Usuario o contrasena incorrectos.', status=400)
    if not user.is_active:
        return json_error('El usuario esta inactivo.', status=403)

    login(request, user)
    return JsonResponse({'user': user_to_dict(user)})


@csrf_exempt
@require_http_methods(['POST'])
def logout_view(request):
    logout(request)
    return JsonResponse({'status': 'ok'})


@require_http_methods(['GET'])
def me_view(request):
    auth_error = require_authenticated(request)
    if auth_error:
        return auth_error
    return JsonResponse({'user': user_to_dict(request.user)})


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH'])
def parent_portal(request):
    auth_error = require_authenticated(request)
    if auth_error:
        return auth_error
    if not request.user.is_parent:
        return json_error('Este portal es solo para padres.', status=403)

    try:
        parent = request.user.parent_profile
    except ParentProfile.DoesNotExist:
        return json_error('Tu usuario no tiene perfil de padre asociado.', status=404)

    if request.method in ['PUT', 'PATCH']:
        data = request_data(request)
        if data is None:
            return json_error('El JSON enviado no es valido.')

        if data.get('action') == 'change_password':
            current_password = data.get('current_password') or ''
            new_password = data.get('new_password') or ''
            confirm_password = data.get('confirm_password') or ''
            if not request.user.check_password(current_password):
                return json_error('La contrasena actual no es correcta.')
            if len(new_password) < 8:
                return json_error('La nueva contrasena debe tener al menos 8 caracteres.')
            if new_password != confirm_password:
                return json_error('La confirmacion no coincide.')

            request.user.set_password(new_password)
            request.user.save()
            update_session_auth_hash(request, request.user)
            return JsonResponse({'updated': True})

        required = request.method == 'PUT'
        first_name = (data.get('first_name') or '').strip()
        last_name = (data.get('last_name') or '').strip()
        phone = (data.get('phone') or '').strip()
        if required and (not first_name or not last_name or not phone):
            return json_error('Nombres, apellidos y telefono son obligatorios.')

        user = parent.user
        if first_name or required:
            user.first_name = first_name
        if last_name or required:
            user.last_name = last_name
        if 'email' in data:
            user.email = (data.get('email') or '').strip()
        user.save()

        for field in ['phone', 'address', 'emergency_phone']:
            if field in data:
                setattr(parent, field, (data.get(field) or '').strip())
        parent.save()
        return JsonResponse(parent_to_dict(parent))

    children = Student.objects.filter(parent=parent).select_related('parent__user', 'class_group')
    payments = Payment.objects.filter(student__parent=parent).select_related(
        'student__parent__user',
        'student__class_group',
    )
    attendance = AttendanceRecord.objects.filter(student__parent=parent).select_related(
        'student__parent__user',
        'student__class_group',
        'session__class_group',
    )
    progress = ProgressEvaluation.objects.filter(student__parent=parent).select_related('student__parent__user', 'student__class_group')
    announcements = Announcement.objects.filter(is_active=True).filter(parent__isnull=True) | Announcement.objects.filter(is_active=True, parent=parent)
    return JsonResponse({
        'parent': parent_to_dict(parent),
        'children': [student_to_dict(student) for student in children],
        'payments': [payment_to_dict(payment) for payment in payments],
        'attendance': [{
            **attendance_record_to_dict(record),
            'session': {
                'id': record.session.id,
                'date': record.session.date.isoformat(),
                'class_group': class_group_to_dict(record.session.class_group),
            },
        } for record in attendance],
        'progress': [progress_to_dict(item) for item in progress],
        'announcements': [announcement_to_dict(item) for item in announcements.order_by('-created_at')],
    })


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def parents_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    User = get_user_model()

    if request.method == 'GET':
        parents = ParentProfile.objects.select_related('user').prefetch_related('children')
        return JsonResponse({'results': [parent_to_dict(parent) for parent in parents]})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    dni = (data.get('dni') or '').strip()
    email = (data.get('email') or '').strip()

    if not first_name or not last_name or not phone or not dni:
        return json_error('Nombres, apellidos, telefono y DNI son obligatorios.')

    username_base = dni
    username = ''.join(char.lower() for char in username_base if char.isalnum() or char in '._-')
    username = username or f'padre{User.objects.count() + 1}'
    original_username = username
    suffix = 1
    while User.objects.filter(username=username).exists():
        suffix += 1
        username = f'{original_username}{suffix}'

    user = User.objects.create_user(
        username=username,
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=data.get('password') or f'P{dni}',
        role=User.Role.PARENT,
    )
    parent = ParentProfile.objects.create(
        user=user,
        dni=dni,
        phone=phone,
        address=(data.get('address') or '').strip(),
        emergency_phone=(data.get('emergency_phone') or '').strip(),
    )
    return JsonResponse(parent_to_dict(parent), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def parent_detail(request, parent_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    try:
        parent = ParentProfile.objects.select_related('user').prefetch_related('children').get(id=parent_id)
    except ParentProfile.DoesNotExist:
        return json_error('Padre no encontrado.', status=404)

    if request.method == 'GET':
        return JsonResponse(parent_to_dict(parent))

    if request.method == 'DELETE':
        if parent.children.exists():
            return json_error('No puedes eliminar un padre con alumnos asociados.', status=400)
        user = parent.user
        parent.delete()
        user.delete()
        return JsonResponse({'deleted': True})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    required = request.method == 'PUT'
    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    phone = (data.get('phone') or '').strip()
    if required and (not first_name or not last_name or not phone):
        return json_error('Nombres, apellidos y telefono son obligatorios.')

    user = parent.user
    if first_name or required:
        user.first_name = first_name
    if last_name or required:
        user.last_name = last_name
    if 'email' in data:
        user.email = (data.get('email') or '').strip()
    user.save()

    for field in ['dni', 'phone', 'address', 'emergency_phone']:
        if field in data:
            setattr(parent, field, (data.get(field) or '').strip())
    parent.save()
    return JsonResponse(parent_to_dict(parent))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def students_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    if request.method == 'GET':
        students = Student.objects.select_related('parent__user', 'class_group')
        return JsonResponse({'results': [student_to_dict(student) for student in students]})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    try:
        parent = ParentProfile.objects.select_related('user').get(id=data.get('parent_id'))
    except ParentProfile.DoesNotExist:
        return json_error('Selecciona un padre valido.')

    first_name = (data.get('first_name') or '').strip()
    last_name = (data.get('last_name') or '').strip()
    birth_date = (data.get('birth_date') or '').strip()

    if not first_name or not last_name or not birth_date:
        return json_error('Nombres, apellidos y fecha de nacimiento son obligatorios.')

    class_group = None
    if data.get('class_group_id'):
        try:
            class_group = ClassGroup.objects.get(id=data.get('class_group_id'))
        except ClassGroup.DoesNotExist:
            return json_error('Selecciona un grupo valido.')

    student = Student.objects.create(
        parent=parent,
        class_group=class_group,
        first_name=first_name,
        last_name=last_name,
        birth_date=birth_date,
        weight_kg=data.get('weight_kg') or None,
        height_cm=data.get('height_cm') or None,
        medical_notes=(data.get('medical_notes') or '').strip(),
        teacher_notes=(data.get('teacher_notes') or '').strip(),
    )
    student.refresh_from_db()
    return JsonResponse(student_to_dict(student), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def student_detail(request, student_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    try:
        student = Student.objects.select_related('parent__user', 'class_group').get(id=student_id)
    except Student.DoesNotExist:
        return json_error('Alumno no encontrado.', status=404)

    if request.method == 'GET':
        return JsonResponse(student_to_dict(student))

    if request.method == 'DELETE':
        student.delete()
        return JsonResponse({'deleted': True})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    required = request.method == 'PUT'
    if required and not all(data.get(field) for field in ['parent_id', 'first_name', 'last_name', 'birth_date']):
        return json_error('Padre, nombres, apellidos y fecha de nacimiento son obligatorios.')

    if 'parent_id' in data:
        try:
            student.parent = ParentProfile.objects.get(id=data.get('parent_id'))
        except ParentProfile.DoesNotExist:
            return json_error('Selecciona un padre valido.')

    if 'class_group_id' in data:
        if data.get('class_group_id'):
            try:
                student.class_group = ClassGroup.objects.get(id=data.get('class_group_id'))
            except ClassGroup.DoesNotExist:
                return json_error('Selecciona un grupo valido.')
        else:
            student.class_group = None

    for field in ['first_name', 'last_name', 'birth_date', 'status', 'weight_kg', 'height_cm', 'medical_notes', 'teacher_notes']:
        if field in data:
            value = data.get(field)
            if field in ['weight_kg', 'height_cm'] and value == '':
                value = None
            if isinstance(value, str) and field not in ['birth_date', 'status']:
                value = value.strip()
            setattr(student, field, value)

    student.save()
    student.refresh_from_db()
    return JsonResponse(student_to_dict(student))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def class_groups_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    if request.method == 'GET':
        groups = ClassGroup.objects.prefetch_related('students')
        return JsonResponse({'results': [class_group_to_dict(group) for group in groups]})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    days = request_group_days(data)
    start_time = request_group_time(data, 'start_time')
    end_time = request_group_time(data, 'end_time')
    if not data.get('name') or not days or not start_time or not end_time:
        return json_error('Nombre, dias, inicio y fin son obligatorios.')
    if start_time >= end_time:
        return json_error('La hora de inicio debe ser menor a la hora de fin.')

    collision = find_group_collision(days, start_time, end_time)
    if collision:
        return json_error(f'El horario se cruza con {collision.name}.')

    group = ClassGroup.objects.create(
        name=(data.get('name') or '').strip(),
        day_of_week=days[0],
        days_of_week=days,
        start_time=start_time,
        end_time=end_time,
        capacity=data.get('capacity') or 12,
        age_range=(data.get('age_range') or '').strip(),
        color=data.get('color') or '#0d7467',
    )
    group.refresh_from_db()
    return JsonResponse(class_group_to_dict(group), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def class_group_detail(request, group_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    try:
        group = ClassGroup.objects.prefetch_related('students').get(id=group_id)
    except ClassGroup.DoesNotExist:
        return json_error('Horario no encontrado.', status=404)

    if request.method == 'GET':
        return JsonResponse(class_group_to_dict(group))

    if request.method == 'DELETE':
        if group.students.exists():
            return json_error('No puedes eliminar un horario con alumnos asignados.', status=400)
        group.delete()
        return JsonResponse({'deleted': True})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    required = request.method == 'PUT'
    days = request_group_days(data, current_group=group)
    start_time = request_group_time(data, 'start_time', current_group=group)
    end_time = request_group_time(data, 'end_time', current_group=group)
    if required and (not data.get('name') or not days or not start_time or not end_time):
        return json_error('Nombre, dias, inicio y fin son obligatorios.')
    if not days or not start_time or not end_time:
        return json_error('Dias, inicio y fin son obligatorios.')
    if start_time >= end_time:
        return json_error('La hora de inicio debe ser menor a la hora de fin.')

    collision = find_group_collision(days, start_time, end_time, exclude_id=group.id)
    if collision:
        return json_error(f'El horario se cruza con {collision.name}.')

    group.day_of_week = days[0]
    group.days_of_week = days
    group.start_time = start_time
    group.end_time = end_time
    for field in ['name', 'capacity', 'age_range', 'color', 'is_active']:
        if field in data:
            value = data.get(field)
            if isinstance(value, str) and field in ['name', 'age_range']:
                value = value.strip()
            setattr(group, field, value)
    group.save()
    group.refresh_from_db()
    return JsonResponse(class_group_to_dict(group))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def payments_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    if request.method == 'GET':
        payments = Payment.objects.select_related('student__parent__user', 'student__class_group')
        return JsonResponse({'results': [payment_to_dict(payment) for payment in payments]})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    try:
        student = Student.objects.get(id=data.get('student_id'))
    except Student.DoesNotExist:
        return json_error('Selecciona un alumno valido.')

    amount = data.get('amount')
    due_date = (data.get('due_date') or '').strip()
    if not amount or not due_date:
        return json_error('Monto y fecha de vencimiento son obligatorios.')

    payment = Payment.objects.create(
        student=student,
        concept=(data.get('concept') or 'Mensualidad').strip(),
        amount=amount,
        due_date=due_date,
        paid_date=data.get('paid_date') or None,
        status=data.get('status') or Payment.Status.PENDING,
        notes=(data.get('notes') or '').strip(),
    )
    payment.refresh_from_db()
    return JsonResponse(payment_to_dict(payment), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def payment_detail(request, payment_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    try:
        payment = Payment.objects.select_related('student__parent__user', 'student__class_group').get(id=payment_id)
    except Payment.DoesNotExist:
        return json_error('Pago no encontrado.', status=404)

    if request.method == 'GET':
        return JsonResponse(payment_to_dict(payment))

    if request.method == 'DELETE':
        payment.delete()
        return JsonResponse({'deleted': True})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')

    required = request.method == 'PUT'
    if required and not all(data.get(field) for field in ['student_id', 'concept', 'amount', 'due_date']):
        return json_error('Alumno, concepto, monto y vencimiento son obligatorios.')

    if 'student_id' in data:
        try:
            payment.student = Student.objects.get(id=data.get('student_id'))
        except Student.DoesNotExist:
            return json_error('Selecciona un alumno valido.')

    for field in ['concept', 'amount', 'due_date', 'paid_date', 'status', 'notes']:
        if field in data:
            value = data.get(field)
            if field == 'paid_date' and value == '':
                value = None
            if isinstance(value, str) and field in ['concept', 'notes']:
                value = value.strip()
            setattr(payment, field, value)

    payment.save()
    payment.refresh_from_db()
    return JsonResponse(payment_to_dict(payment))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def attendance_sessions_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error

    if request.method == 'GET':
        sessions = AttendanceSession.objects.select_related('class_group').prefetch_related('records__student__parent__user', 'records__student__class_group')
        return JsonResponse({'results': [attendance_session_to_dict(session) for session in sessions]})

    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    try:
        group = ClassGroup.objects.get(id=data.get('class_group_id'))
    except ClassGroup.DoesNotExist:
        return json_error('Selecciona un grupo valido.')

    session, _ = AttendanceSession.objects.get_or_create(
        class_group=group,
        date=data.get('date') or date.today(),
        defaults={'notes': (data.get('notes') or '').strip()},
    )
    for student in group.students.filter(status=Student.Status.ACTIVE):
        AttendanceRecord.objects.get_or_create(session=session, student=student)
    session.refresh_from_db()
    return JsonResponse(attendance_session_to_dict(session), status=201)


@csrf_exempt
@require_http_methods(['PATCH'])
def attendance_record_detail(request, record_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    try:
        record = AttendanceRecord.objects.select_related('student__parent__user', 'student__class_group', 'session__class_group').get(id=record_id)
    except AttendanceRecord.DoesNotExist:
        return json_error('Registro de asistencia no encontrado.', status=404)
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    if data.get('status'):
        record.status = data.get('status')
    if 'notes' in data:
        record.notes = (data.get('notes') or '').strip()
    record.save()
    return JsonResponse(attendance_record_to_dict(record))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def progress_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    if request.method == 'GET':
        evaluations = ProgressEvaluation.objects.select_related('student__parent__user', 'student__class_group')
        return JsonResponse({'results': [progress_to_dict(item) for item in evaluations]})
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    try:
        student = Student.objects.get(id=data.get('student_id'))
    except Student.DoesNotExist:
        return json_error('Selecciona un alumno valido.')
    evaluation = ProgressEvaluation.objects.create(
        student=student,
        date=data.get('date') or date.today(),
        weight_kg=data.get('weight_kg') or None,
        height_cm=data.get('height_cm') or None,
        strength=data.get('strength') or 0,
        endurance=data.get('endurance') or 0,
        coordination=data.get('coordination') or 0,
        flexibility=data.get('flexibility') or 0,
        notes=(data.get('notes') or '').strip(),
    )
    evaluation.refresh_from_db()
    return JsonResponse(progress_to_dict(evaluation), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def progress_detail(request, progress_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    try:
        evaluation = ProgressEvaluation.objects.select_related('student__parent__user', 'student__class_group').get(id=progress_id)
    except ProgressEvaluation.DoesNotExist:
        return json_error('Evaluacion no encontrada.', status=404)
    if request.method == 'GET':
        return JsonResponse(progress_to_dict(evaluation))
    if request.method == 'DELETE':
        evaluation.delete()
        return JsonResponse({'deleted': True})
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    for field in ['date', 'weight_kg', 'height_cm', 'strength', 'endurance', 'coordination', 'flexibility', 'notes']:
        if field in data:
            value = data.get(field)
            if field in ['weight_kg', 'height_cm'] and value == '':
                value = None
            if field == 'notes':
                value = (value or '').strip()
            setattr(evaluation, field, value)
    evaluation.save()
    evaluation.refresh_from_db()
    return JsonResponse(progress_to_dict(evaluation))


@csrf_exempt
@require_http_methods(['GET', 'POST'])
def announcements_collection(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    if request.method == 'GET':
        announcements = Announcement.objects.select_related('parent__user')
        return JsonResponse({'results': [announcement_to_dict(item) for item in announcements]})
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    title = (data.get('title') or '').strip()
    body = (data.get('body') or '').strip()
    if not title or not body:
        return json_error('Titulo y mensaje son obligatorios.')
    parent = None
    if data.get('parent_id'):
        try:
            parent = ParentProfile.objects.get(id=data.get('parent_id'))
        except ParentProfile.DoesNotExist:
            return json_error('Padre no encontrado.')
    announcement = Announcement.objects.create(
        title=title,
        body=body,
        audience=Announcement.Audience.PARENT if parent else Announcement.Audience.ALL,
        parent=parent,
        is_active=data.get('is_active', True),
    )
    return JsonResponse(announcement_to_dict(announcement), status=201)


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH', 'DELETE'])
def announcement_detail(request, announcement_id):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    try:
        announcement = Announcement.objects.select_related('parent__user').get(id=announcement_id)
    except Announcement.DoesNotExist:
        return json_error('Comunicado no encontrado.', status=404)
    if request.method == 'GET':
        return JsonResponse(announcement_to_dict(announcement))
    if request.method == 'DELETE':
        announcement.delete()
        return JsonResponse({'deleted': True})
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    for field in ['title', 'body', 'is_active']:
        if field in data:
            value = data.get(field)
            if isinstance(value, str):
                value = value.strip()
            setattr(announcement, field, value)
    if 'parent_id' in data:
        announcement.parent = ParentProfile.objects.filter(id=data.get('parent_id')).first() if data.get('parent_id') else None
        announcement.audience = Announcement.Audience.PARENT if announcement.parent else Announcement.Audience.ALL
    announcement.save()
    return JsonResponse(announcement_to_dict(announcement))


@csrf_exempt
@require_http_methods(['GET', 'PUT', 'PATCH'])
def settings_detail(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    setting = get_settings()
    if request.method == 'GET':
        return JsonResponse(setting_to_dict(setting))
    data = request_data(request)
    if data is None:
        return json_error('El JSON enviado no es valido.')
    for field in ['academy_name', 'teacher_name', 'phone', 'address', 'default_monthly_fee']:
        if field in data:
            value = data.get(field)
            if isinstance(value, str) and field != 'default_monthly_fee':
                value = value.strip()
            if field == 'default_monthly_fee' and value == '':
                value = 0
            setattr(setting, field, value)
    setting.save()
    return JsonResponse(setting_to_dict(setting))


@require_http_methods(['GET'])
def reports_summary(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    attendance_counts = AttendanceRecord.objects.values('status').annotate(total=Count('id'))
    return JsonResponse({
        'students_active': Student.objects.filter(status=Student.Status.ACTIVE).count(),
        'payments_pending': Payment.objects.filter(status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]).count(),
        'income_total': str(Payment.objects.filter(status=Payment.Status.PAID).aggregate(total=Sum('amount'))['total'] or 0),
        'attendance': list(attendance_counts),
        'progress_evaluations': ProgressEvaluation.objects.count(),
    })


@require_http_methods(['GET'])
def reports_export(request):
    permission_error = require_teacher(request)
    if permission_error:
        return permission_error
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(['Alumno', 'Padre', 'Grupo', 'Estado', 'Pagos pendientes'])
    for student in Student.objects.select_related('parent__user', 'class_group').prefetch_related('payments'):
        writer.writerow([
            str(student),
            student.parent.user.get_full_name(),
            student.class_group.name if student.class_group else '',
            student.get_status_display(),
            student.payments.filter(status__in=[Payment.Status.PENDING, Payment.Status.OVERDUE]).count(),
        ])
    response = HttpResponse(output.getvalue(), content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sisfitkids-reporte.csv"'
    return response
