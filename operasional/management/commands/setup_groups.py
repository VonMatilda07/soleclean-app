from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from operasional.models import Order, OrderItem, Customer, Service, Pengeluaran

class Command(BaseCommand):
    help = 'Setup user groups and permissions for RBAC'

    def handle(self, *args, **kwargs):
        # Get content types
        order_ct = ContentType.objects.get_for_model(Order)
        orderitem_ct = ContentType.objects.get_for_model(OrderItem)
        pengeluaran_ct = ContentType.objects.get_for_model(Pengeluaran)
        customer_ct = ContentType.objects.get_for_model(Customer)

        # Create Groups
        admin_group, created = Group.objects.get_or_create(name='Admin')
        teknisi_group, created = Group.objects.get_or_create(name='Teknisi')
        supervisor_group, created = Group.objects.get_or_create(name='Supervisor')
        customer_group, created = Group.objects.get_or_create(name='Customer')

        # Clear existing permissions
        admin_group.permissions.clear()
        teknisi_group.permissions.clear()
        supervisor_group.permissions.clear()
        customer_group.permissions.clear()

        # Assign sensible model permissions so admin UI shows them and
        # Django model-level checks (if used) will work.

        # Admin: full access to related models
        admin_perms = Permission.objects.filter(
            content_type__in=[order_ct, orderitem_ct, pengeluaran_ct, customer_ct]
        )
        admin_group.permissions.set(admin_perms)

        # Supervisor: can view orders, add orders, view customers, view expenses
        supervisor_perms = []
        for codename in ['view_order', 'add_order', 'view_customer', 'view_pengeluaran']:
            try:
                supervisor_perms.append(Permission.objects.get(codename=codename))
            except Permission.DoesNotExist:
                pass
        supervisor_group.permissions.set(supervisor_perms)

        # Teknisi: can add orders and update order items (status), and view orders
        teknisi_perms = []
        for codename in ['add_order', 'change_orderitem', 'view_order']:
            try:
                teknisi_perms.append(Permission.objects.get(codename=codename))
            except Permission.DoesNotExist:
                pass
        teknisi_group.permissions.set(teknisi_perms)

        # Customer: no model permissions (tracking is public)
        customer_group.permissions.clear()

        self.stdout.write(
            self.style.SUCCESS('✅ Successfully setup 4 groups: Admin, Teknisi, Supervisor, Customer')
        )
        self.stdout.write(
            self.style.WARNING(
                '\n📝 Next steps:\n'
                '1. Go to /admin/auth/user/\n'
                '2. Add users and assign them to groups\n'
                '3. Admin: Full access\n'
                '4. Teknisi: Update order status, manage expenses\n'
                '5. Supervisor: View analytics, manage finances\n'
                '6. Customer: View own orders\n'
            )
        )
