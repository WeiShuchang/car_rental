from django.shortcuts import render
from administrator.models import Driver, ChatRoom, Message, Reservation
from django.http import JsonResponse
from django.db.models import Q, Count
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json


@login_required
def driver_dashboard(request):
    try:
        driver = Driver.objects.get(user=request.user)
    except Driver.DoesNotExist:
        return render(request, 'driver/driver_not_found.html')

    # Get all chat rooms for this driver with unread count
    chat_rooms = ChatRoom.objects.filter(
        reservation__driver=driver
    ).annotate(
        unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=request.user))
    ).select_related(
        'reservation', 
        'reservation__user'
    ).prefetch_related(
        'messages'
    ).order_by('-updated_at')

    # Calculate total unread count
    total_unread = sum(room.unread_count for room in chat_rooms)

    context = {
        'driver': driver,
        'chat_rooms': chat_rooms,
        'total_unread': total_unread,
    }

    return render(request, 'driver/driver_dashboard.html', context)

@login_required
@require_POST
def send_message(request):
    try:
        data = json.loads(request.body)
        room_id = data.get('room_id')
        content = data.get('message')
        
        # Verify the driver has access to this chat room
        chat_room = ChatRoom.objects.get(
            reservation__id=room_id,
            reservation__driver__user=request.user
        )
        
        # Create the message
        message = Message.objects.create(
            chat_room=chat_room,
            sender=request.user,
            content=content
        )
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'timestamp': message.timestamp.strftime('%H:%M'),
                'sender': request.user.id
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
@require_POST
def mark_messages_read(request, room_id):
    try:
        # Verify the driver has access to this chat room
        chat_room = ChatRoom.objects.get(
            reservation__id=room_id,
            reservation__driver__user=request.user
        )
        
        # Mark messages as read
        Message.objects.filter(
            chat_room=chat_room,
            is_read=False
        ).exclude(
            sender=request.user
        ).update(is_read=True)
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@login_required
def get_messages(request, room_id):
    try:
        # Verify the driver has access to this chat room
        chat_room = ChatRoom.objects.get(
            reservation__id=room_id,
            reservation__driver__user=request.user
        )
        
        messages = chat_room.messages.all().order_by('timestamp')
        
        message_list = [{
            'id': msg.id,
            'content': msg.content,
            'timestamp': msg.timestamp.strftime('%H:%M'),
            'sender': msg.sender.id,
            'is_read': msg.is_read
        } for msg in messages]
        
        return JsonResponse({
            'success': True,
            'messages': message_list
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
    
@login_required
def driver_approved_reservations(request):
    # Get reservations where:
    # - the driver is the current user (through driver.user)
    # - status is 'approved'
    reservations = Reservation.objects.filter(
        driver__user=request.user,
        status='approved'
    ).order_by('start_date')
    
    return render(request, 'driver/driver_approved_reservations.html', {
        'reservations': reservations
    })


@login_required
def driver_completed_reservations(request):
    # Get reservations where:
    # - the driver is the current user
    # - status is 'completed'
    reservations = Reservation.objects.filter(
        driver__user=request.user,
        status='completed'
    ).order_by('-end_date')  # Newest first
    
    return render(request, 'driver/driver_completed_reservations.html', {
        'reservations': reservations
    })