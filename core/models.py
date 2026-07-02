from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        TEACHER = 'TEACHER', 'Profesor'
        PARENT = 'PARENT', 'Padre'

    role = models.CharField(max_length=20, choices=Role.choices, default=Role.PARENT)

    @property
    def is_teacher(self):
        return self.role == self.Role.TEACHER

    @property
    def is_parent(self):
        return self.role == self.Role.PARENT


class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='parent_profile')
    dni = models.CharField('DNI', max_length=12, blank=True)
    phone = models.CharField('telefono', max_length=20, blank=True)
    address = models.CharField('direccion', max_length=180, blank=True)
    emergency_phone = models.CharField('telefono de emergencia', max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'padre'
        verbose_name_plural = 'padres'

    def __str__(self):
        full_name = self.user.get_full_name()
        return full_name or self.user.username


class ClassGroup(models.Model):
    class Day(models.IntegerChoices):
        MONDAY = 1, 'Lunes'
        TUESDAY = 2, 'Martes'
        WEDNESDAY = 3, 'Miercoles'
        THURSDAY = 4, 'Jueves'
        FRIDAY = 5, 'Viernes'
        SATURDAY = 6, 'Sabado'
        SUNDAY = 7, 'Domingo'

    name = models.CharField('nombre', max_length=80)
    day_of_week = models.PositiveSmallIntegerField('dia', choices=Day.choices)
    start_time = models.TimeField('hora de inicio')
    end_time = models.TimeField('hora de fin')
    capacity = models.PositiveSmallIntegerField('cupos', default=12)
    age_range = models.CharField('rango de edad', max_length=40, blank=True)
    is_active = models.BooleanField('activo', default=True)

    class Meta:
        verbose_name = 'grupo'
        verbose_name_plural = 'grupos'
        ordering = ['day_of_week', 'start_time', 'name']

    def __str__(self):
        return f'{self.name} - {self.get_day_of_week_display()} {self.start_time:%H:%M}'


class Student(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Activo'
        PAUSED = 'PAUSED', 'Pausado'
        RETIRED = 'RETIRED', 'Retirado'

    parent = models.ForeignKey(ParentProfile, on_delete=models.PROTECT, related_name='children')
    class_group = models.ForeignKey(
        ClassGroup,
        on_delete=models.SET_NULL,
        related_name='students',
        null=True,
        blank=True,
    )
    first_name = models.CharField('nombres', max_length=80)
    last_name = models.CharField('apellidos', max_length=80)
    birth_date = models.DateField('fecha de nacimiento')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    weight_kg = models.DecimalField('peso kg', max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField('talla cm', max_digits=5, decimal_places=2, null=True, blank=True)
    medical_notes = models.TextField('notas medicas', blank=True)
    teacher_notes = models.TextField('observaciones del profesor', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'alumno'
        verbose_name_plural = 'alumnos'
        ordering = ['last_name', 'first_name']

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pendiente'
        PAID = 'PAID', 'Pagado'
        OVERDUE = 'OVERDUE', 'Vencido'

    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    concept = models.CharField('concepto', max_length=90, default='Mensualidad')
    amount = models.DecimalField('monto', max_digits=8, decimal_places=2)
    due_date = models.DateField('fecha de vencimiento')
    paid_date = models.DateField('fecha de pago', null=True, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'pago'
        verbose_name_plural = 'pagos'
        ordering = ['-due_date', 'student__last_name']

    def __str__(self):
        return f'{self.student} - {self.concept} ({self.get_status_display()})'


class AttendanceSession(models.Model):
    class_group = models.ForeignKey(ClassGroup, on_delete=models.CASCADE, related_name='attendance_sessions')
    date = models.DateField('fecha')
    notes = models.TextField('notas', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'sesion de asistencia'
        verbose_name_plural = 'sesiones de asistencia'
        ordering = ['-date', 'class_group__day_of_week']
        unique_together = ('class_group', 'date')

    def __str__(self):
        return f'{self.class_group} - {self.date:%Y-%m-%d}'


class AttendanceRecord(models.Model):
    class Status(models.TextChoices):
        PRESENT = 'PRESENT', 'Presente'
        ABSENT = 'ABSENT', 'Falta'
        LATE = 'LATE', 'Tardanza'
        JUSTIFIED = 'JUSTIFIED', 'Justificado'

    session = models.ForeignKey(AttendanceSession, on_delete=models.CASCADE, related_name='records')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_records')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PRESENT)
    notes = models.CharField('notas', max_length=160, blank=True)

    class Meta:
        verbose_name = 'registro de asistencia'
        verbose_name_plural = 'registros de asistencia'
        unique_together = ('session', 'student')

    def __str__(self):
        return f'{self.student} - {self.session.date:%Y-%m-%d} ({self.get_status_display()})'


class ProgressEvaluation(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='progress_evaluations')
    date = models.DateField('fecha')
    weight_kg = models.DecimalField('peso kg', max_digits=5, decimal_places=2, null=True, blank=True)
    height_cm = models.DecimalField('talla cm', max_digits=5, decimal_places=2, null=True, blank=True)
    strength = models.PositiveSmallIntegerField('fuerza', default=0)
    endurance = models.PositiveSmallIntegerField('resistencia', default=0)
    coordination = models.PositiveSmallIntegerField('coordinacion', default=0)
    flexibility = models.PositiveSmallIntegerField('flexibilidad', default=0)
    notes = models.TextField('observaciones', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'evaluacion de progreso'
        verbose_name_plural = 'evaluaciones de progreso'
        ordering = ['-date', 'student__last_name']

    def __str__(self):
        return f'{self.student} - {self.date:%Y-%m-%d}'


class Announcement(models.Model):
    class Audience(models.TextChoices):
        ALL = 'ALL', 'Todos'
        PARENT = 'PARENT', 'Padre especifico'

    title = models.CharField('titulo', max_length=120)
    body = models.TextField('mensaje')
    audience = models.CharField(max_length=20, choices=Audience.choices, default=Audience.ALL)
    parent = models.ForeignKey(ParentProfile, on_delete=models.CASCADE, related_name='announcements', null=True, blank=True)
    is_active = models.BooleanField('activo', default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'comunicado'
        verbose_name_plural = 'comunicados'
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class AppSetting(models.Model):
    academy_name = models.CharField('academia', max_length=120, default='SIS Fit Kids')
    teacher_name = models.CharField('profesor', max_length=120, default='Profesor Principal')
    phone = models.CharField('telefono', max_length=30, blank=True)
    address = models.CharField('direccion', max_length=180, blank=True)
    default_monthly_fee = models.DecimalField('mensualidad por defecto', max_digits=8, decimal_places=2, default=0)

    class Meta:
        verbose_name = 'configuracion'
        verbose_name_plural = 'configuracion'

    def __str__(self):
        return self.academy_name
