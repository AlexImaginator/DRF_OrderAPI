from django.dispatch import receiver, Signal
from django.core.mail import send_mail
from users.models import User


new_order = Signal()
orders_in_shop = Signal()
order_status_change = Signal()


@receiver(new_order)
def new_order_signal(user_id, orders, **kwargs):
    user = User.objects.get(id=user_id)
    email_adress = user.email
    subject = 'Order creating'
    str_order = []
    for order in orders:
        str_part = f'Shop {order["Shop"]} - order ID {order["Order ID"]}'
        str_order.append(str_part)
    order_msg = ', '.join(str_order)
    message = f'New order was created. Order: {order_msg}'
    from_email = 'shopbackend@email.ru'
    send_mail(subject, message, from_email, [email_adress, ])

@receiver(orders_in_shop)
def orders_in_shop_signal(user_id, context, **kwargs):
    user = User.objects.get(id=user_id)
    email_adress = user.email
    subject = 'Orders in shop'
    from_email = 'shopbackend@email.ru'
    for order in context:
        message = f'''
Shop {order["shop_id"]}, order {order["order_id"]}
        
Order state: {order["order_state"]}, created at {order["order_created_at"]}
        
Customer: {order["order_user"]}, contacts: {order["order_contact"]}
        
Positions: {order["order_positions"]}
        '''
    send_mail(subject, message, from_email, [email_adress, ])

@receiver(order_status_change)
def order_status_change_signal(user_id, order_id, new_state, **kwargs):
    user = User.objects.get(id=user_id)
    email_adress = user.email
    subject = 'Orders status changed'
    from_email = 'shopbackend@email.ru'
    message = f'Your order {order_id} status has been changed: {new_state}'
    send_mail(subject, message, from_email, [email_adress, ])
