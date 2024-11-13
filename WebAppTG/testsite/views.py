from django.contrib.auth import login, authenticate, get_user_model, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound, Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.template.loader import render_to_string, get_template
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import ListView, DetailView, CreateView
from .models import *
from .forms import *
from django.db.models import Q, Avg, Min, Max, Sum
from django.core.mail import send_mail
from random import random, randrange, randint
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from .token import *
from itertools import chain
from datetime import datetime, timedelta
import itertools
import time
from pytz import timezone
import requests
import urllib.parse
from urllib.request import urlopen
# from WebAppTG.decorators import log_function_call
from django.core.cache import cache
from PIL import Image
import io
from .services.rate_calculator import RateCalc

#
def chat(request, num):
    Request_data = Requests.objects.get(pk=num)
    Request_data.Status = 'План'
    Order_data = Orders.objects.get(pk=Request_data.OrderID)
    Order_data.Status = 'План'

    Deals.objects.create(TG_Contact=request.user, RequestID=num, OrderID=Request_data.OrderID, PCCNTR=Request_data.PCCNTR,
                         ExchangePointID=Request_data.ExchangePointID)
    Deals_data = Deals.objects.get(TG_Contact=request.user, RequestID=num, OrderID=Request_data.OrderID, PCCNTR=Request_data.PCCNTR,
                         ExchangePointID=Request_data.ExchangePointID)
    Request_data.DealID = Deals_data.pk
    Request_data.save()
    Order_data.DealID = Deals_data.pk
    Order_data.RequestID = Request_data.pk
    Order_data.save()
    Chats.objects.create(Send_User=request.user, Receive_User=Request_data.ExchangePointID, OrderID=Request_data.OrderID,
                        RequestID=Request_data.pk, DealID=Deals_data.pk)

    partner_contacts = Users_PCCNTR.objects.get(PCCNTR=Request_data.PCCNTR, ContactType='PART')
    Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                 PCCNTR=Request_data.PCCNTR, ExchangePointID='-',
                                 Text='Предложение по заявке на обмен №' + str(
                                     Request_data.OrderID) + ' было принято клиентом')
    mail_subject = 'Выбор предложения на обмен'
    email = User.objects.filter(username=partner_contacts.TG_Contact).values_list('email', flat=True)[0]
    to_email = email
    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
    html_content = get_template(
        'testsite/send_notification_to_PCCNTR_request_accept.html').render({
        'user': partner_contacts.TG_Contact,
        'OrderNum': Request_data.OrderID,
    })
    msg.attach_alternative(html_content, "text/html")
    res = msg.send()

    org_contacts = Users_PCCNTR.objects.get(PCCNTR=Request_data.PCCNTR, ContactType='ORG',
                                            ExchangePointID__contains=Request_data.ExchangePointID)
    if org_contacts.TG_Contact != partner_contacts.TG_Contact:
        Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                     PCCNTR=Request_data.PCCNTR,
                                     ExchangePointID=Request_data.ExchangePointID,
                                     Text='Предложение по заявке на обмен №' + str(
                                         Request_data.OrderID) + ' было принято клиентом')
        mail_subject = 'Выбор предложения на обмен'
        email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email', flat=True)[0]
        to_email = email
        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
        html_content = get_template(
            'testsite/send_notification_to_PCCNTR_request_accept.html').render({
            'user': org_contacts.TG_Contact,
            'OrderNum': Request_data.OrderID,
        })
        msg.attach_alternative(html_content, "text/html")
        res = msg.send()

    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
    empl_contacts = (Users_PCCNTR.objects.filter(PCCNTR=Request_data.PCCNTR,
                                                 ContactType__in=job_positions,
                                                 ExchangePointID__contains=Request_data.ExchangePointID)
                     .values('TG_Contact', 'ContactType'))
    for empl in empl_contacts:
        if empl['TG_Contact'] != partner_contacts.TG_Contact and empl['TG_Contact'] != org_contacts.TG_Contact:
            Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                         ContactType=empl['ContactType'],
                                         PCCNTR=Request_data.PCCNTR,
                                         ExchangePointID=Request_data.ExchangePointID,
                                         Text='Предложение по заявке на обмен №' + str(
                                             Request_data.OrderID) + ' было принято клиентом')
            mail_subject = 'Выбор предложения на обмен'
            email = User.objects.filter(username=empl['TG_Contact']).values_list('email', flat=True)[0]
            to_email = email
            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
            html_content = get_template(
                'testsite/send_notification_to_PCCNTR_request_accept.html').render({
                'user': empl['TG_Contact'],
                'OrderNum': Request_data.OrderID,
            })
            msg.attach_alternative(html_content, "text/html")
            res = msg.send()

    All_requests = Requests.objects.filter(OrderID=Request_data.OrderID).exclude(pk=Request_data.pk).values_list('pk', flat=True)
    for request_pk in All_requests:
        request_data = Requests.objects.get(pk=request_pk)
        request_data.Status = 'Отмена'
        request_data.save()
        DealReserve_data = DealReserve.objects.get(PCCNTR=request_data.PCCNTR,OrderID=request_data.OrderID,RequestID=request_data.pk)
        PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data.PCCNTR)
        PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
        DealReserve.objects.filter(PCCNTR=request_data.PCCNTR,OrderID=request_data.OrderID,RequestID=request_data.pk).delete()
        PCCNTR_data.save()
        partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data.PCCNTR, ContactType='PART')
        Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                     PCCNTR=request_data.PCCNTR, ExchangePointID='-',
                                     Text='Предложение по заявке на обмен №' + str(
                                         request_data.OrderID) + ' было отклонено по причине выбора клиентом другого предложения')
        mail_subject = 'Отклонение предложения на обмен'
        email = User.objects.filter(username=partner_contacts.TG_Contact).values_list('email', flat=True)[0]
        to_email = email
        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
        html_content = get_template(
            'testsite/send_notification_to_PCCNTR_request_decline.html').render({
            'user': partner_contacts.TG_Contact,
            'OrderNum': request_data.OrderID,
        })
        msg.attach_alternative(html_content, "text/html")
        res = msg.send()

        org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data.PCCNTR, ContactType='ORG',
                                                ExchangePointID__contains=request_data.ExchangePointID)
        if org_contacts.TG_Contact != partner_contacts.TG_Contact:
            Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                         PCCNTR=request_data.PCCNTR,
                                         ExchangePointID=request_data.ExchangePointID,
                                         Text='Предложение по заявке на обмен №' + str(
                                             request_data.OrderID) + ' было отклонено по причине выбора клиентом другого предложения')
            mail_subject = 'Отклонение предложения на обмен'
            email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email', flat=True)[0]
            to_email = email
            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
            html_content = get_template(
                'testsite/send_notification_to_PCCNTR_request_decline.html').render({
                'user': org_contacts.TG_Contact,
                'OrderNum': request_data.OrderID,
            })
            msg.attach_alternative(html_content, "text/html")
            res = msg.send()

        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        empl_contacts = (Users_PCCNTR.objects.filter(PCCNTR=request_data.PCCNTR,
                                                    ContactType__in=job_positions,
                                                    ExchangePointID__contains=request_data.ExchangePointID)
                                                        .values('TG_Contact', 'ContactType'))
        for empl in empl_contacts:
            if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                'TG_Contact'] != org_contacts.TG_Contact:
                Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                             ContactType=empl['ContactType'],
                                             PCCNTR=request_data.PCCNTR,
                                             ExchangePointID=request_data.ExchangePointID,
                                             Text='Предложение по заявке на обмен №' + str(
                                                 request_data.OrderID) + ' было отклонено по причине выбора клиентом другого предложения')
                mail_subject = 'Отклонение предложения на обмен'
                email = User.objects.filter(username=empl['TG_Contact']).values_list('email', flat=True)[0]
                to_email = email
                msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                html_content = get_template(
                    'testsite/send_notification_to_PCCNTR_request_decline.html').render({
                    'user': empl['TG_Contact'],
                    'OrderNum': request_data.OrderID,
                })
                msg.attach_alternative(html_content, "text/html")
                res = msg.send()

    return redirect('room', str(Deals_data.pk))
    # return render(request, 'testsite/chat.html')

#
def room(request, room_name):
    if cache.get('user_type') != 'Партнер' and cache.get('user_type') != 'Клиент':  # and user_type != 'Организатор'
        ExchangeName = cache.get('ExchangeName')
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=cache.get('user_type')).values('ContactType_code')[0][
            'ContactType_code']

    chat_data = Chats.objects.get(DealID=room_name)
    Request_data = Requests.objects.get(DealID=room_name)
    Order_data = Orders.objects.get(DealID=room_name)
    Deal_data = Deals.objects.get(pk=room_name)

    ExchangeType = ExchangeID.objects.get(pk=Order_data.ExchangeID).Name_RUS
    if Order_data.SendTransferType == "CSH":
        p_t_b = "Наличные"
    elif Order_data.SendTransferType == "CRP":
        p_t_b = "Перевод по сети блокчейн"
    elif Order_data.SendTransferType == "CRD":
        p_t_b = "Карточный перевод"

    if Order_data.ReceiveTransferType == "CSH":
        p_t_s = "Наличные"
    elif Order_data.ReceiveTransferType == "CRP":
        p_t_s = "Перевод по сети блокчейн"
    elif Order_data.ReceiveTransferType == "CRD":
        p_t_s = "Карточный перевод"

    Deal_Country = Countries.objects.get(Country_code=Order_data.Country).Name_RUS
    Deal_City = Cities.objects.get(City_code=Order_data.City).Name_RUS
    # Добавить стоиомсть обмена (как в доске объявлений
    Deal_info = {'num': Deal_data.pk, 'ExchangeType': ExchangeType,
                 'SendAmount': str(Request_data.SendAmount) + ' ' + Order_data.SendCurrencyISO,
                 'ReceiveAmount': str(Request_data.ReceiveAmount)  + ' ' + Order_data.ReceiveCurrencyISO,
                 'SendTransferType': p_t_b, 'FinOfficeFrom': Order_data.FinOfficeFrom,
                 'ReceiveTransferType': p_t_s, 'FinOfficeTo': Order_data.FinOfficeTo,
                 'OrderDate': Order_data.OrderDate, 'TimeInterval': Order_data.TimeInterval,
                 'Country': Deal_Country, 'City': Deal_City, 'DeliveryType': Order_data.DeliveryType,
                 'OrderLimit': Order_data.OrderLimit, 'SendCurrencyISO': Order_data.SendCurrencyISO,
                 'Comment': Order_data.Comment}


    # print(request.user)
    # print(chat_data.Send_User)
    # print(request.user != chat_data.Send_User)
    if request.user != chat_data.Send_User and cache.get('user_type') != 'Клиент' and (len(Users_PCCNTR.objects.filter(TG_Contact=request.user, ExchangePointID__contains=chat_data.Receive_User).values_list('pk', flat=True)) != 0 or len(Users_PCCNTR.objects.filter(TG_Contact=request.user, PCCNTR=PCCNTR_ExchP.objects.get(ExchangePointID=chat_data.Receive_User).PCCNTR).values_list('pk', flat=True)) != 0):
        send_user = chat_data.Receive_User
        receive_user = chat_data.Send_User
    elif cache.get('user_type') == 'Клиент':
        send_user = request.user
        receive_user = chat_data.Receive_User
    # try:
    #     receive_user = Chats.objects.filter(pk=chat_code).values_list('Receive_User', flat=True)[0]
    # except:
    #     receive_user = Chats.objects.filter(pk=chat_code).values_list('Send_User', flat=True)[0]
    # print(send_user)

    Messages_data = Messages.objects.filter(Chat_code=chat_data.pk).values('Send_User', 'Receive_User', 'Text', 'MessageType').order_by('MessageTime')
    # for message in Messages_data:
    #     print(send_user)
    #     print(message['Send_User'])
    #     print(str(send_user) == message['Send_User'])
    # print(send_user)
    # print(receive_user)
    return render(request, 'testsite/room.html', {
        'room_name': room_name,
        'send_user': str(send_user),
        'receive_user': str(receive_user),
        'chat_code': chat_data.pk,
        'Messages': Messages_data,
        'usertype': usertype,
        'current_user': str(send_user),
        'Deal_info': Deal_info
    })

#
def send_message(request):
    message_data = json.loads(request.body)
    # print(message_data)
    Messages.objects.create(Chat_code = message_data['chat_code_1'], Send_User = message_data['send_user_1'],
                            Receive_User = message_data['receive_user_1'], Text = message_data['text_1'],
                            MessageType='Text')
    return HttpResponse("Text was added!")

#
def send_file(request):
    message_data = json.loads(request.body)
    # print(message_data)
    Messages.objects.create(Chat_code = message_data['chat_code_1'], Send_User = message_data['send_user_1'],
                            Receive_User = message_data['receive_user_1'], Text = message_data['text_1'],
                            MessageType='File')
    return HttpResponse("File was added!")

#
def success(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type != 'Партнер' and user_type != 'Клиент':  # and user_type != 'Организатор'
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    context = {
        'usertype': usertype,
    }
    return render(request, 'testsite/success.html', context=context)

#
def index(request, usertype):
    # global user_type, ExchangeName
    username = request.user
    try:
        user_type = cache.get('user_type')
    except:
        pass
    if usertype == 'CLI':
        user_type = ContactType.objects.filter(ContactType_code=usertype).values('Name_RUS')[0][
            'Name_RUS']
        user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
        usertype_new = usertype
        usertype2 = ContactType.objects.filter(ContactType_code=usertype).values('Name_RUS')[0]['Name_RUS']
        pcc_name = ''
        ExchangeName = ''
        param = 1
        cache.set('user_type', user_type)
        unread_notifications = int(Notifications.objects.filter(TG_Contact=username, ContactType = usertype, Unread=False).count())

    elif usertype == 'PART':
        user_type = ContactType.objects.filter(ContactType_code=usertype).values('Name_RUS')[0][
            'Name_RUS']
        user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
        user_2 = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'ExchangePointID',
                                                                         'ACTIVE', 'ContactType', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=user_2[0]['PCCNTR']).PCCNTR_name
        usertype2 = ContactType.objects.filter(ContactType_code=usertype).values('Name_RUS')[0]['Name_RUS']
        usertype_new = usertype
        cache.set('user_type', user_type)
        ExchangeName = ''
        param = 2
        unread_notifications = int(Notifications.objects.filter(TG_Contact=username, ContactType=usertype, Unread=False).count())

    elif user_type == 'Сотрудник обменника':
        user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
        ExchangeName = usertype
        ExchangeName = urllib.parse.unquote(ExchangeName)

        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID', flat=True)
        user_pccntr = Users_PCCNTR.objects.get(TG_Contact=username, ContactType__in=job_positions,
                                               ExchangePointID__in=EPID)
        pcc_name = PCCNTR.objects.get(PCCNTR_code=user_pccntr.PCCNTR).PCCNTR_name
        usertype_new = 'EMPL'
        cache.set('ExchangeName', ExchangeName)
        if ';' in user_pccntr.ContactType:
            usertype2 = 'Куратор, Курьер'
        else:
            usertype2 = ContactType.objects.filter(ContactType_code=user_pccntr.ContactType).values('Name_RUS')[0][
                'Name_RUS']

        unread_notifications = int(Notifications.objects.filter(TG_Contact=username, ContactType__in=job_positions,Unread=False).count())

        param = 2
        # user_type = ContactType.objects.filter(ContactType_code=user_pccntr.ContactType).values('Name_RUS')[0]['Name_RUS']

    elif user_type == 'Организатор':
        ExchangeName = usertype
        ExchangeName = urllib.parse.unquote(ExchangeName)
        user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
        pcc_code = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values('PCCNTR')[0]['PCCNTR']
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc_code).PCCNTR_name
        usertype2 = user_type
        usertype_new = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
        param = 2
        cache.set('ExchangeName', ExchangeName)
        unread_notifications = int(Notifications.objects.filter(TG_Contact=username, ContactType = ContactType.objects.filter(Name_RUS=user_type).
                                        values('ContactType_code')[0]['ContactType_code'], Unread=False).count())

    if (param == 2) or ((param == 1) and (len(Users_PCCNTR.objects.filter(TG_Contact=username).values('ContactType')) != 0)):
        param_page = 1
    else:
        param_page = 0

    context = {
        'activity_parameter': user_1[0]['ACTIVE'],
        'username': str(user_1[0]['Name']),
        'usertype': usertype_new,
        'usertype2': usertype2,
        'PCCNTR_name': pcc_name,
        'ExchangePoint_name': ExchangeName,
        'param_page': param_page,
        'unread_notifications': unread_notifications
    }
    return render(request, 'testsite/index.html', context=context)

#
def Notification(request):
    # global ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type == 'Организатор':
        usertype = ExchangeName
        Notification_data = Notifications.objects.filter(TG_Contact=request.user,
                                                         ContactType=ContactType.objects.filter(Name_RUS=user_type).
                                                         values('ContactType_code')[0]['ContactType_code']).values('pk',
                                                                                                                   'Unread',
                                                                                                                   'Text',
                                                                                                                   'NoticeDate').order_by(
            '-NoticeDate')
    elif user_type == 'Сотрудник обменника':
        usertype = ExchangeName
        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        Notification_data = Notifications.objects.filter(TG_Contact=request.user,
                                                         ContactType__in=job_positions).values('pk','Unread', 'Text','NoticeDate').order_by(
            '-NoticeDate')
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
        Notification_data = Notifications.objects.filter(TG_Contact=request.user,
                                                         ContactType=ContactType.objects.filter(Name_RUS=user_type).
                                                         values('ContactType_code')[0]['ContactType_code']).values('pk',
                                                                                                                   'Unread',
                                                                                                                   'Text',
                                                                                                                   'NoticeDate').order_by(
            '-NoticeDate')


    url = 'http://ipinfo.io/json'
    response = urlopen(url)
    ip_data = json.load(response)
    d = pytz.timezone(ip_data['timezone']) # or some other local date

    for Notification in Notification_data:
        unique_notice = Notifications.objects.get(pk=Notification['pk'])
        if unique_notice.Unread == False:
            unique_notice.Unread = True
            unique_notice.save()
        if Notification['NoticeDate'].tzinfo != ip_data['timezone']:
            # Конвертировать время в новый часовой пояс
            mess_date = d.normalize(Notification['NoticeDate'].astimezone(d))
            # Формат даты в новом часовом поясе
            Notification['NoticeDate'] = mess_date.strftime("%d.%m.%Y %H:%M")

    return render(request, 'testsite/notifications.html', context={'usertype': usertype, 'Notifications': Notification_data})

#
def Confirm_order_changes(request, num):
    # try:
    full_request = Requests.objects.get(pk=num, Active=False)
    full_request.Active = True
    full_request.save()
    Notifications_Data = Notifications.objects.filter(PCCNTR=full_request.PCCNTR,
                                                      Text__contains = 'внес изменения в заявку на обмен №' + str(full_request.OrderID)).values_list('pk', flat=True)
    for Notification_pk in Notifications_Data:
        full_notification = Notifications.objects.get(pk=Notification_pk)
        if '<br> <div style="text-align:center; "><button style="background-color: lawngreen; font-size: 12px">  <a href=' in full_notification.Text:
            full_notification.Text = full_notification.Text[:full_notification.Text.find('<br> <div style="text-align:center; "><button style="background-color: lawngreen; font-size: 12px">  <a href=')]
            full_notification.Text = full_notification.Text + ' <p style="text-align:center; "> <font color="#32CD32">Изменения приняты!</font> </p>'
            full_notification.save()
    client_contacts = Users.objects.get(TG_Contact = Orders.objects.get(pk=full_request.OrderID).TG_Contact)
    Notifications.objects.create(TG_Contact=client_contacts.TG_Contact, ContactType='CLI',
                                 PCCNTR='-', ExchangePointID='-',
                                 Text='Обменник ' + str(PCCNTR_ExchP.objects.get(ExchangePointID=full_request.ExchangePointID).ExchangePointName) + ' принял изменения по заявке на обмен №'
                                      + str(full_request.OrderID))

    mail_subject = 'Изменения в заявке на обмен'
    email = User.objects.filter(username=client_contacts.TG_Contact).values_list('email', flat=True)[0]
    to_email = email
    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
    html_content = get_template('testsite/send_notification_to_client_confirm_change_order.html').render({
        'ExchangePointName': PCCNTR_ExchP.objects.get(ExchangePointID=full_request.ExchangePointID).ExchangePointName,
        'Client': client_contacts.TG_Contact,
        'OrderNum': full_request.OrderID,
    })
    msg.attach_alternative(html_content, "text/html")
    res = msg.send()
    return redirect('Notification')
    # except:
    #     return redirect('Notification')
    # Прописать цикл удаления кнопок из текста и добавления зеленого текста "Изменения приняты"

#
def Decline_order_changes(request, num):
    # try:
    full_request = Requests.objects.get(pk=num, Active=False)
    Notifications_Data = Notifications.objects.filter(PCCNTR=full_request.PCCNTR,
        Text__contains='внес изменения в заявку на обмен №' + str(full_request.OrderID)).values_list('pk', flat=True)
    for Notification_pk in Notifications_Data:
        full_notification = Notifications.objects.get(pk=Notification_pk)
        if '<br> <div style="text-align:center; "><button style="background-color: lawngreen; font-size: 12px">  <a href=' in full_notification.Text:
            full_notification.Text = full_notification.Text[:full_notification.Text.find(
                '<br> <div style="text-align:center; "><button style="background-color: lawngreen; font-size: 12px">  <a href=')]
            full_notification.Text = full_notification.Text + ' <p style="text-align:center; "> <font color="#DC143C">Изменения отклонены и предложение удалено!</font> </p>'
            full_notification.save()
    DealReserve_data = DealReserve.objects.get(PCCNTR=full_request.PCCNTR, OrderID=full_request.OrderID,
                                               RequestID=full_request.pk)
    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=full_request.PCCNTR)
    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
    DealReserve.objects.filter(PCCNTR=full_request.PCCNTR, OrderID=full_request.OrderID,
                               RequestID=full_request.pk).delete()
    PCCNTR_data.save()
    Requests.objects.filter(pk=num).delete()
    client_contacts = Users.objects.get(TG_Contact = Orders.objects.get(pk=full_request.OrderID).TG_Contact)
    Notifications.objects.create(TG_Contact=client_contacts.TG_Contact, ContactType='CLI',
                                 PCCNTR='-', ExchangePointID='-',
                                 Text='Обменник ' + str(PCCNTR_ExchP.objects.get(ExchangePointID=full_request.ExchangePointID).ExchangePointName) + ' отклонил изменения по заявке на обмен №'
                                      + str(full_request.OrderID))

    mail_subject = 'Изменения в заявке на обмен'
    email = User.objects.filter(username=client_contacts.TG_Contact).values_list('email', flat=True)[0]
    to_email = email
    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
    html_content = get_template('testsite/send_notification_to_client_decline_change_order.html').render({
        'ExchangePointName': PCCNTR_ExchP.objects.get(ExchangePointID=full_request.ExchangePointID).ExchangePointName,
        'Client': client_contacts.TG_Contact,
        'OrderNum': full_request.OrderID,
    })
    msg.attach_alternative(html_content, "text/html")
    res = msg.send()
    return redirect('Notification')
    # except:
    #     return redirect('Notification')

    # Прописать цикл удаления кнопок из текста и добавления зеленого текста "Изменения отклонены и предлодение удалено"

#
def check_usertype(request):
    # global user_type
    username = request.user
    user_pccntr = Users_PCCNTR.objects.filter(TG_Contact=username).values('ACTIVE', 'ContactType')
    if len(user_pccntr) == 0:
        user_type = 'Клиент'
        # cache.set('user_type', user_type)
        return redirect('home', 'CLI')
    else:
        usertypes = ['Клиент']
        for user in user_pccntr:
            if '; ' in user['ContactType']:
                usertypes.append('Куратор')
            else:
                user_contacttype = \
                ContactType.objects.filter(ContactType_code=user['ContactType']).values('Name_RUS')[0][
                    'Name_RUS']
                usertypes.append(user_contacttype)
        usertypes = list(set(list(usertypes)))
        usertypes.sort()

        context = {
            'username': username,
            'usertypes': usertypes,
        }
        return render(request, 'testsite/check_usertype.html', context=context)

#
def choose_exchange(request, usertype):
    # global user_type
    username = request.user
    if usertype == 'EMPL':
        user_type = 'Сотрудник обменника'
        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        EPIDs = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType__in=job_positions).values_list(
            'ExchangePointID', flat=True)
    elif usertype == 'ORG':
        user_type = 'Организатор'
        ExchangePointIDs = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=usertype).values_list(
            'ExchangePointID', flat=True)
        EPIDs = []
        for ExchangePointID in ExchangePointIDs:
            if ';' in ExchangePointID:
                while ";" in ExchangePointID:
                    ID = ExchangePointID[:ExchangePointID.find(";")].strip()
                    EPIDs.append(ID)
                    ExchangePointID = ExchangePointID[ExchangePointID.find(";") + 1:].strip()
                EPIDs.append(ExchangePointID.strip())
            else:
                EPIDs.append(ExchangePointID.strip())
        EPIDs = list(set(EPIDs))

    cache.set('user_type', user_type)
    EPs_info = PCCNTR_ExchP.objects.filter(ExchangePointID__in=EPIDs).values_list('ExchangePointName',
                                                                                  flat=True).order_by(
        'ExchangePointName').distinct()

    context = {
        'username': username,
        'EPs_info': EPs_info,
    }
    return render(request, 'testsite/choose_exchange.html', context=context)

#
def safety(request):
    # global  ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type != 'Партнер' and user_type != 'Клиент':
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    return render(request, 'testsite/settings_safety.html', context={'usertype': usertype})

#
def passwordreset(request):
    # global user, user_email, code_check
    if request.method == 'POST':
        form = Emailforreset(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            try:
                user = User.objects.get(email=email)
                user_email = email
                code_check = randint(10000, 99999)
                cache.set('user_email', user_email)
                cache.set('code_check', code_check)
                mail_subject = 'Код для сброса пароля'
                reason = 'сброса пароля'
                message = render_to_string('testsite/acc_active_email.html', {
                    'user': user,
                    'reason': reason,
                    'code': code_check,
                })
                to_email = email
                send_mail(mail_subject, message, "ya.maxrov@ya.ru", [to_email], fail_silently=False, )
                return redirect('email_confirm', 2)
            except:
                form = Emailforreset()
                error = 'Пользователь с данным email не зарегистрирован в системе'
        else:
            form = Emailforreset()
            error = ''
    else:
        form = Emailforreset()
        error = ''
    return render(request, 'testsite/password_reset.html',
                  {'form': form, 'title': 'Забыли пароль?', 'error': error})

#
class RegisterUser(CreateView):
    # global user, user_name, user_password, code_check, user_email
    form_class = RegisterUserForm
    template_name = 'testsite/register1.html'
    # @log_function_call
    def form_valid(self, form):
        # global user, user_name, user_password, code_check, user_email
        username = self.request.POST['username']
        password = self.request.POST['password2']
        email = self.request.POST['email']
        user = User.objects.create_user(username=username, password=password, email=email, is_active=False)
        user.save()
        user_name = username
        user_password = password
        user_email = email
        code_check = randint(10000, 99999)
        mail_subject = 'Код для подтверждения регистрации'
        reason = 'подтверждения регистрации'
        message = render_to_string('testsite/acc_active_email.html', {
            'user': user,
            'reason': reason,
            'code': code_check,
        })
        to_email = self.request.POST['email']
        cache.set('user_name', user_name)
        cache.set('user_password', user_password)
        cache.set('code_check', code_check)
        cache.set('user_email', user_email)
        send_mail(mail_subject, message, "ya.maxrov@ya.ru", [to_email], fail_silently=False, )
        return redirect('email_confirm', 1)

# # @log_function_call
def email_confirm(request, num):
    # global user, user_name, user_password, code_check, user_email, checked_username
    user_name = cache.get('user_name')
    user_password = cache.get('user_password')
    code_check = cache.get('code_check')
    user_email = cache.get('user_email')
    checked_username = cache.get('checked_username')
    if request.method == 'POST':
        form = Emailconfirm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            if int(code) == int(code_check):
                if num == 1:
                    user = User.objects.get(username=user_name)
                    user.is_active = True
                    user.save()
                    userauth = authenticate(username=user_name, password=user_password)
                    #print(userauth)
                    if userauth is not None:
                        if userauth.is_active:
                            login(request, userauth)
                            #user_name = ""
                            cache.delete('user_password')
                            cache.delete('user_email')
                            return redirect('register2')
                        else:
                            form = Emailconfirm()
                            error = ""
                    else:
                        form = Emailconfirm()
                        error = ""

                elif num == 2:
                    user = User.objects.get(email=user_email)
                    token = password_reset_token.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    cache.delete('user_email')
                    return redirect('password_reset_confirm', uid, token)

                elif num == 3:
                    user = User.objects.get(username=request.user)
                    user.email = user_email
                    cache.delete('user_email')
                    user.save()
                    return redirect('email_reset_complete')

                elif num == 4:
                    return redirect('general_settings_exchange_structure_new_1_final')

                elif num == 5:
                    return redirect('general_settings_exchange_structure_new_3_final')

                elif num == 6:
                    return redirect('general_settings_change_exchange_structure_1_final')

            else:
                code_check = randint(10000, 99999)
                cache.set('code_check', code_check)
                if num == 1:
                    mail_subject = 'Код для подтверждения регистрации'
                    reason = 'подтверждения регистрации'
                    title = 'Подтверждение регистрации'

                elif num == 2:
                    user_name = request.user
                    mail_subject = 'Код для сброса пароля'
                    reason = 'сброса пароля'
                    title = 'Подтверждение email для сброса пароля'

                elif num == 3:
                    user_name = request.user
                    mail_subject = 'Код для подтверждения нового email'
                    reason = 'подтверждения нового email'
                    title = 'Подтверждение нового email'

                elif num == 4 or num == 6:
                    user = User.objects.get(username=checked_username)
                    title = 'Подтверждение регистрации пользователя как "Организатор"'
                    mail_subject = 'Код для подтверждения регистрации пользователя как "Организатор"'
                    reason = 'регистрации пользователя как "Организатор"'


                elif num == 5 or num == 7:
                    user = User.objects.get(username=checked_username)
                    title = 'Подтверждение регистрации пользователя как сотрудника обменника'
                    mail_subject = 'Код для подтверждения регистрации пользователя как сотрудника обменника'
                    reason = 'регистрации пользователя как сотрудника обменника'

                message = render_to_string('testsite/acc_active_email.html', {
                    'user': user,
                    'reason': reason,
                    'code': code_check,
                })
                if num == 4 or num == 5 or num == 6 or num == 7:
                    to_email = user.email
                else:
                    to_email = user_email
                send_mail(
                    mail_subject,
                    message,
                    "ya.maxrov@ya.ru",
                    [to_email],
                    fail_silently=False,
                )
                form = Emailconfirm()
                error = "Неверный код, введите новый"
    else:
        if num == 1:
            title = 'Подтверждение регистрации'
            reason = 'подтверждения регистрации'
        elif num == 2:
            title = 'Подтверждение email для сброса пароля'
            reason = 'сброса пароля'
        elif num == 3:
            title = 'Подтверждение нового email'
            reason = 'подтверждения нового email'
        elif num == 4 or num == 6:
            title = 'Подтверждение регистрации пользователя как "Организатор"'
            reason = 'регистрации пользователя как "Организатор"'
        elif num == 5 or num == 7:
            title = 'Подтверждение регистрации пользователя как сотрудника обменника'
            reason = 'регистрации пользователя как сотрудника обменника'
        form = Emailconfirm()
        error = ""
    return render(request, 'testsite/email_confirm.html',
                  {'title': title, 'reason': reason, 'form': form, 'error': error, 'num': num})

#
def email_confirm_repeat(request, num):
    # global user, user_name, user_password, code_check, user_email, checked_username
    user_name = cache.get('user_name')
    user_password = cache.get('user_password')
    code_check = cache.get('code_check')
    user_email = cache.get('user_email')
    checked_username = cache.get('checked_username')
    if request.method == 'POST':
        form = Emailconfirm(request.POST)
        if form.is_valid():
            code = form.cleaned_data.get('code')
            if int(code) == int(code_check):
                if num == 1:
                    user = User.objects.get(username=user_name)
                    user.is_active = True
                    user.save()
                    userauth = authenticate(username=user_name, password=user_password)
                    # print(userauth)
                    if userauth is not None:
                        if userauth.is_active:
                            login(request, userauth)
                            # user_name = ""
                            cache.delete('user_password')
                            cache.delete('user_email')
                            return redirect('register2')
                        else:
                            form = Emailconfirm()
                            error = ""
                    else:
                        form = Emailconfirm()
                        error = ""

                elif num == 2:
                    user = User.objects.get(email=user_email)
                    token = password_reset_token.make_token(user)
                    uid = urlsafe_base64_encode(force_bytes(user.pk))
                    cache.delete('user_email')
                    return redirect('password_reset_confirm', uid, token)

                elif num == 3:
                    user = User.objects.get(username=request.user)
                    user.email = user_email
                    cache.delete('user_email')
                    user.save()
                    return redirect('email_reset_complete')

                elif num == 4:
                    return redirect('general_settings_exchange_structure_new_1_final')

                elif num == 5:
                    return redirect('general_settings_exchange_structure_new_3_final')

                elif num == 6:
                    return redirect('general_settings_change_exchange_structure_1_final')

            else:
                code_check = randint(10000, 99999)
                cache.set('code_check', code_check)
                if num == 1:
                    mail_subject = 'Код для подтверждения регистрации'
                    reason = 'подтверждения регистрации'
                    title = 'Подтверждение регистрации'

                elif num == 2:
                    user_name = request.user
                    mail_subject = 'Код для сброса пароля'
                    reason = 'сброса пароля'
                    title = 'Подтверждение email для сброса пароля'

                elif num == 3:
                    user_name = request.user
                    mail_subject = 'Код для подтверждения нового email'
                    reason = 'подтверждения нового email'
                    title = 'Подтверждение нового email'

                elif num == 4 or num == 6:
                    user = User.objects.get(username=checked_username)
                    title = 'Подтверждение регистрации пользователя как "Организатор"'
                    mail_subject = 'Код для подтверждения регистрации пользователя как "Организатор"'
                    reason = 'регистрации пользователя как "Организатор"'


                elif num == 5 or num == 7:
                    user = User.objects.get(username=checked_username)
                    title = 'Подтверждение регистрации пользователя как сотрудника обменника'
                    mail_subject = 'Код для подтверждения регистрации пользователя как сотрудника обменника'
                    reason = 'регистрации пользователя как сотрудника обменника'

                message = render_to_string('testsite/acc_active_email.html', {
                    'user': user,
                    'reason': reason,
                    'code': code_check,
                })
                if num == 4 or num == 5 or num == 6 or num == 7:
                    to_email = user.email
                else:
                    to_email = user_email
                send_mail(
                    mail_subject,
                    message,
                    "ya.maxrov@ya.ru",
                    [to_email],
                    fail_silently=False,
                )
                form = Emailconfirm()
                error = "Неверный код, введите новый"
    else:
        code_check = randint(10000, 99999)
        cache.set('code_check', code_check)
        if num == 1:
            mail_subject = 'Код для подтверждения регистрации'
            reason = 'подтверждения регистрации'
            title = 'Подтверждение регистрации'

        elif num == 2:
            user_name = request.user
            mail_subject = 'Код для сброса пароля'
            reason = 'сброса пароля'
            title = 'Подтверждение email для сброса пароля'

        elif num == 3:
            user_name = request.user
            mail_subject = 'Код для подтверждения нового email'
            reason = 'подтверждения нового email'
            title = 'Подтверждение нового email'

        elif num == 4 or num == 6:
            title = 'Подтверждение регистрации пользователя как "Организатор"'
            user = User.objects.get(username=checked_username)
            mail_subject = 'Код для подтверждения регистрации пользователя как "Организатор"'
            reason = 'регистрации пользователя как "Организатор"'

        elif num == 5 or num == 7:
            user = User.objects.get(username=checked_username)
            title = 'Подтверждение регистрации пользователя как сотрудника обменника'
            mail_subject = 'Код для подтверждения регистрации пользователя как сотрудника обменника'
            reason = 'регистрации пользователя как сотрудника обменника'

        message = render_to_string('testsite/acc_active_email.html', {
            'user': user,
            'reason': reason,
            'code': code_check,
        })
        if num == 4 or num == 5 or num == 6 or num == 7:
            to_email = user.email
        else:
            to_email = user_email
        send_mail(
            mail_subject,
            message,
            "ya.maxrov@ya.ru",
            [to_email],
            fail_silently=False,
        )
        form = Emailconfirm()
        error = ""
    return render(request, 'testsite/email_confirm.html',
                  {'title': title, 'reason': reason, 'form': form, 'error': error, 'num': num})

# @log_function_call
def emailreset(request):
    # global user, user_email, code_check
    if request.method == 'POST':
        form = Emailforreset(request.POST)
        if form.is_valid():
            username = request.user
            user = User.objects.get(username=username)
            user_email = form.cleaned_data.get('email')
            code_check = randint(10000, 99999)
            cache.set('user_email')
            cache.set('code_check')
            mail_subject = 'Код для подтверждения нового email'
            reason = 'подтверждения нового email'
            message = render_to_string('testsite/acc_active_email.html', {
                'user': user,
                'reason': reason,
                'code': code_check,
            })
            to_email = user_email
            send_mail(mail_subject, message, "ya.maxrov@ya.ru", [to_email], fail_silently=False, )
            return redirect('email_confirm', 3)
        else:
            form = Emailforreset()
            error = ''
    else:
        form = Emailforreset()
        error = ''
    return render(request, 'testsite/email_reset.html', {'form': form, 'title': 'Смена email', 'error': error})

#
def emailresetcomplete(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type != 'Партнер' and user_type != 'Клиент':  # and user_type != 'Организатор'
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    context = {
        'usertype': usertype,
    }
    return render(request, 'testsite/email_reset_complete.html', context=context)

#
def delete_user(request):
    # global user_name
    #print(user_name)
    user_name = cache.get('user_name')
    User.objects.filter(username=user_name).delete()
    cache.delete('user_name')
    return redirect('register')

#
def delete_user_2(request):
    # global user_name
    #print(user_name)
    user_name = cache.get('user_name')
    Users.objects.filter(TG_Contact=user_name).delete()
    Users_PCCNTR.objects.filter(TG_Contact=user_name).delete()
    return redirect('register2')

#
def delete_pccntr(request):
    # global pcc_code
    pcc_code = cache.get('pcc_code')
    PCCNTR.objects.filter(PCCNTR_code=pcc_code).delete()
    cache.delete('pcc_code')
    return redirect('register_pccntr')

#
def delete_org(request):
    # global checked_username, pcc_code
    pcc_code = cache.get('pcc_code')
    checked_username = cache.get('checked_username')
    Users_PCCNTR.objects.filter(PCCNTR=pcc_code, TG_Contact=checked_username, ContactType='ORG').delete()
    cache.delete('checked_username')
    return redirect('general_settings_exchange_structure_new_1')

#
def delete_exch(request):
    # global pcc_code
    pcc_code = cache.get('pcc_code')
    PCCNTR_ExchP.objects.filter(PCCNTR=pcc_code).delete()
    return redirect('general_settings_exchange_structure_new_2')

#
def delete_empl(request):
    # global pcc_code
    pcc_code = cache.get('pcc_code')
    job_positions = ['COUR', 'CUR', 'COUR; CUR', 'CUR; COUR']
    Users_PCCNTR.objects.filter(PCCNTR=pcc_code, ContactType__in=job_positions).delete()
    return redirect('general_settings_exchange_structure_new_3', 1)

#
def delete_exch_operations(request, exch_name):
    # global pcc_code
    pcc_code = cache.get('pcc_code')
    EP_ExchangeID.objects.filter(PCCNTR=pcc_code).delete()
    PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_code).delete()
    return redirect('general_settings_exchange_deals_new', exch_name)

#
def general_settings(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
        param = 0
        ExchangeName = ''
    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'ORG':
        param = 1
    context = {
        "param": param,
        'usertype': ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'],
        'ExchangeName': ExchangeName
    }
    return render(request, 'testsite/settings_general.html', context=context)

#
def general_settings_pccntr(request):
    # global user_type
    user_type = cache.get('user_type')
    username = request.user
    #print(user_type)
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    if request.method == 'POST':
        form = AddPCCNTRName(request.POST)
        if form.is_valid():
            if str(form.cleaned_data['PCCNTR_name']) != str(pcc_name.PCCNTR_name):
                PCCNTRs = PCCNTR.objects.filter(PCCNTR_name=form.cleaned_data['PCCNTR_name']).all()
                if len(PCCNTRs) == 0:
                    pcc_name.PCCNTR_name = str(form.cleaned_data['PCCNTR_name'])
                    pcc_name.save()
                else:
                    error = 'Центр прибыли и затрат с данным наименованием уже зарегистрирован в системе'
                    return render(request, 'testsite/register_pccntr.html', {'form': form, 'title': 'Наименование Центра прибыли и затрат', 'param': 1, "usertype": ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'], 'error': error})
            return redirect('general_settings')
    else:
        form = AddPCCNTRName(initial={'PCCNTR_name': pcc_name.PCCNTR_name})
    return render(request, 'testsite/register_pccntr.html',
                  {'form': form, 'title': 'Наименование Центра прибыли и затрат', 'param': 1,
                   "usertype": ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                       'ContactType_code']})

#
def general_settings_exchange_points(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user

    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=
        ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']).values(
            'TG_Contact', 'PCCNTR', 'ContactType', 'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат
        param3 = 0
        ExchangePoints = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("ExchangePointName",
                                                                                              flat=True).order_by(
            'ExchangePointName')
        ExchangePoints = list(set(ExchangePoints))
        ExchangePoints.sort()
        ExchangePointswithTransferslist = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
            'ExchangePointID',
            flat=True)
    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'ORG':
        ExchangeName = urllib.parse.unquote(ExchangeName)
        pcc_code = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values('PCCNTR')[0]['PCCNTR']
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc_code).PCCNTR_name
        param3 = 1
        ExchangePoints = [ExchangeName]
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        ExchangePointswithTransferslist = EP_ExchangeID.objects.filter(PCCNTR=pcc_code,
                                                                       ExchangePointID__in=EPID).values_list(
            'ExchangePointID', flat=True)

    ExchangePointswithTransferslist_names = PCCNTR_ExchP.objects.filter(
        ExchangePointID__in=ExchangePointswithTransferslist).values_list("ExchangePointName", flat=True).order_by(
        'ExchangePointName')
    ExchangePointswithTransferslist_names = list(set(ExchangePointswithTransferslist_names))
    ExchangePointswithTransferslist_names.sort()
    if len(ExchangePointswithTransferslist_names) == 0:
        param = 0
    else:
        param = 1

    context = {
        "title": "Настройка обменников",
        "ExchangePoints": ExchangePoints,
        "ExchangePointswithTransfers": ExchangePointswithTransferslist_names,
        "param": param,
        "param3": param3,
    }
    return render(request, 'testsite/settings_general_exchange_points.html', context=context)

#
def general_settings_change_exchange_structure(request, exch_name):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    # ExchangeName = cache.get('ExchangeName')
    username = request.user
    ExchangeName = urllib.parse.unquote(exch_name)
    exch_code = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('pk', flat=True)[0]
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=
    ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
        'ContactType_code']).values('TG_Contact', 'PCCNTR', 'ContactType', 'ExchangePointID')
    if pcc[0]['ContactType'] == 'PART':
        param = 0
        cache.set('ExchangeName', ExchangeName)
    elif pcc[0]['ContactType'] == 'ORG':
        param = 1
    context = {
        "param": param,
        'usertype': ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'],
        'exch_code': exch_code,
        'exch_name': ExchangeName
    }
    return render(request, 'testsite/settings_general_change_exchange_structure_menu.html', context=context)

#
def general_settings_change_exchange_structure_1(request):
    # global checked_username, user_type, ExchangeName, Org_Name
    # user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    Exchange_Point_IDs = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',flat=True).order_by('ExchangePointID')
    if len(Exchange_Point_IDs) == 1:
        Exchange_Point_IDs_string = Exchange_Point_IDs[0]
    else:
        Exchange_Point_IDs_string = str("; ".join(Exchange_Point_IDs))
    Org_Name = str(Users_PCCNTR.objects.filter(ExchangePointID=Exchange_Point_IDs_string, ContactType='ORG').values_list('TG_Contact', flat=True)[0])
    cache.set('Org_Name', Org_Name)
    if request.method == 'POST':
        form = ChooseOrgforExchP(data=request.POST)
        if form.is_valid():
            username = request.user
            find_user = Users.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'))
            if form.cleaned_data.get('UserToCheck') == Org_Name:
                return redirect('general_settings_change_exchange_structure', ExchangeName)
            else:
                if len(find_user) != 0:
                    find_user_1 = Users_PCCNTR.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'),
                                                              ContactType=
                                                              ContactType.objects.filter(Name_RUS='Партнер').values(
                                                                  'ContactType_code')[0]['ContactType_code'])
                    if len(find_user_1) == 0 or (form.cleaned_data.get('UserToCheck') == username):
                        checked_username = form.cleaned_data.get('UserToCheck')
                        cache.set('checked_username', checked_username)
                        return redirect('general_settings_exchange_structure_new_1_confirm', 4)
                    else:
                        error = 'Данный пользователь зарегистрирован в системе как "Партнер"'
                        return render(request, 'testsite/settings_general_exchange_structure_1.html',
                                      {'form': form, 'title': 'Изменение организатора для обменника', 'param': 2, 'param2':1,
                                       'error': error, 'exch_name': ExchangeName})
                else:
                    error = 'Данный пользователь не зарегистрирован в системе как "Клиент"'
                    return render(request, 'testsite/settings_general_exchange_structure_1.html',
                                  {'form': form, 'title': 'Изменение организатора для обменника', 'param': 2, 'param2':1,
                                   'error': error, 'exch_name': ExchangeName})

    else:
        form = ChooseOrgforExchP(initial={'UserToCheck': Org_Name})
    return render(request, 'testsite/settings_general_exchange_structure_1.html',
                  {'form': form, 'title': 'Изменение организатора для обменника', 'param': 2, 'error': "", 'param2':1,
                   'exch_name': ExchangeName})

#
def general_settings_change_exchange_structure_1_final(request):
    # global checked_username, user_type, ExchangeName, Org_Name
    # user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    checked_username = cache.get('checked_username')
    Org_Name = cache.get('Org_Name')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    # pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    chosen_user = Users.objects.get(TG_Contact=checked_username)
    Exchange_Point_IDs = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                                 flat=True).order_by(
        'ExchangePointID')
    if len(Exchange_Point_IDs) == 1:
        Exchange_Point_IDs_string = Exchange_Point_IDs[0]
    else:
        Exchange_Point_IDs_string = str("; ".join(Exchange_Point_IDs))
    previous_org = Users_PCCNTR.objects.get(TG_Contact=Org_Name, ContactType='ORG',
                                            ExchangePointID=Exchange_Point_IDs_string)
    previous_org.TG_Contact = checked_username
    previous_org.COUNTRY = chosen_user.COUNTRY
    previous_org.CITY = chosen_user.CITY
    previous_org.Language = chosen_user.Language
    previous_org.save()
    cache.delete('Org_Name')
    cache.delete('checked_username')
    return redirect('general_settings_change_exchange_structure', ExchangeName)

#
def general_settings_change_exchange_structure_2(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if request.method == 'POST':
        form = ExchPInformation(data=request.POST)
        if form.is_valid():
            username = request.user
            pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
            pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

            ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values('ExchangePointID',
                                                                                                'ExchangePointName',
                                                                                                'ExchangePointCity',
                                                                                                'ExchangePointCountry',
                                                                                                'ExchangePointOfficeCourier').order_by(
                'ExchangePointID')
            exch_OfficeCourier = str("; ".join(form.cleaned_data.get('ExchPOfficeCourier')))
            old_country_codes = []
            new_country_codes = []
            for country in form.cleaned_data.get('ExchPCountry'):
                coun_code = Countries.objects.filter(Name_RUS=country).values('Country_code')[0]['Country_code']
                new_country_codes.append(coun_code)
            new_country_codes.sort()

            for EP in ExchangePoints:
                old_country_codes.append(EP['ExchangePointCountry'])
            old_country_codes.sort()

            ExchP_Names = [ExchangeName]
            if old_country_codes != new_country_codes:
                Old_ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list(
                    'ExchangePointID', flat=True).order_by('ExchangePointID')
                Old_ExchangePoints = list(Old_ExchangePoints)
                Old_ExchangePoints.sort()
                if len(Old_ExchangePoints) == 1:
                    old_exch_point_IDs = Old_ExchangePoints[0]
                else:
                    old_exch_point_IDs = str("; ".join(Old_ExchangePoints))

                job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                for country_code in old_country_codes:
                    if country_code not in new_country_codes:
                        EP = PCCNTR_ExchP.objects.get(ExchangePointName=ExchangeName, ExchangePointCountry=country_code)
                        EP_employees = Users_PCCNTR.objects.filter(ExchangePointID=EP.ExchangePointID,
                                                                   ContactType__in=job_positions).values_list(
                            'TG_Contact', flat=True).order_by('TG_Contact')
                        EP_Deals = EP_ExchangeID.objects.filter(ExchangePointID=EP.ExchangePointID).values_list(
                            'ExchangeTransferID')
                        if len(EP_employees) != 0:
                            #print(EP_employees)
                            error = 'По стране ' + str(
                                Countries.objects.filter(Country_code=country_code).values('Name_RUS')[0][
                                    'Name_RUS']) + " найдены действующие сотрудники. Необходимо уволить всех сотрудников перед удалением обменника."
                            return render(request, 'testsite/settings_general_exchange_structure_2.html',
                                          {'form': form, 'title': 'Орг. структура обменника', 'param': 2, 'param2':1,
                                           'error': error, 'exch_name': ExchangeName})

                        elif len(EP_Deals) != 0:
                            EP_ExchangeID.objects.filter(ExchangePointID=EP.ExchangePointID).delete()
                            # error = 'По стране ' + str(Countries.objects.filter(Country_code=country_code).values('Name_RUS')[0]['Name_RUS']) + " найдены действующие направления сделок. Необходимо удалить все направления сделок перед удалением обменника."
                            # return render(request, 'testsite/settings_general_exchange_structure_2.html',
                            #               {'form': form, 'title': 'Орг. структура обменника', 'param': 2,
                            #                'error': error, 'exch_name': ExchangeName})

                        else:
                            PCCNTR_ExchP.objects.filter(ExchangePointID=EP.ExchangePointID,
                                                        ExchangePointCountry=country_code,
                                                        ExchangePointName=ExchangeName).delete()

                for country_code in new_country_codes:
                    if country_code not in old_country_codes:
                        cities = ''
                        coun_code = country_code
                        count_ExchangePoint = PCCNTR_ExchP.objects.filter(
                            ExchangePointCountry=coun_code).values_list('ExchangePointID', flat=True).order_by(
                            'ExchangePointID')
                        if len(count_ExchangePoint) == 0:
                            quantity_EP = '1'
                        else:
                            last_exchP = count_ExchangePoint[len(count_ExchangePoint) - 1]
                            quantity_EP = str(int(last_exchP[5:]) + 1)

                        ExchPID = str('EP_' + str(coun_code) + quantity_EP.zfill(4))
                        for city in form.cleaned_data.get('ExchPCity'):
                            city_info = Cities.objects.filter(Name_RUS=city).values('City_code', 'Country')
                            if city_info[0]['Country'] == coun_code:
                                cities += str(str(city_info[0]['City_code']) + "; ")
                        cities = cities[:len(cities) - 2]
                        ExchangeTransfers = EP_ExchangeID.objects.filter(
                            ExchangePointID=ExchangePoints[0]['ExchangePointID']).values('ExchangeTransferID',
                                                                                         'ExchTOAmount_Min',
                                                                                         'ExchTOAmount_Max',
                                                                                         'EP_PRFTNORM')
                        for Transfer in ExchangeTransfers:
                            EP_ExchangeID.objects.create(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=ExchPID
                                                         , ExchangeTransferID=Transfer['ExchangeTransferID']
                                                         , ExchTOAmount_Min=Transfer['ExchTOAmount_Min']
                                                         , ExchTOAmount_Max=Transfer['ExchTOAmount_Max']
                                                         , EP_PRFTNORM=Transfer['EP_PRFTNORM'])

                        PCCNTR_ExchP.objects.create(ExchangePointID=ExchPID, PCCNTR=pcc_name.PCCNTR_code,
                                                    ExchangePointCountry=coun_code, ExchangePointCity=cities,
                                                    ExchangePointName=ExchangeName,
                                                    ExchangePointOfficeCourier=exch_OfficeCourier)
                        ExchP_Names.append(form.cleaned_data.get('ExchPName'))

                New_ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list(
                    'ExchangePointID', flat=True).order_by('ExchangePointID')
                New_ExchangePoints = list(New_ExchangePoints)
                New_ExchangePoints.sort()
                if len(New_ExchangePoints) == 1:
                    new_exch_point_IDs = New_ExchangePoints[0]
                else:
                    new_exch_point_IDs = str("; ".join(New_ExchangePoints))
                organizator = Users_PCCNTR.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=old_exch_point_IDs,
                                                       ContactType='ORG')
                organizator.ExchangePointID = new_exch_point_IDs
                organizator.save()

            old_city_codes = []
            new_city_codes = []

            for city in form.cleaned_data.get('ExchPCity'):
                city_code = Cities.objects.filter(Name_RUS=city).values('City_code')[0]['City_code']
                new_city_codes.append(city_code)
            new_city_codes.sort()

            for EP in ExchangePoints:
                if ';' in EP['ExchangePointCity']:
                    City = EP['ExchangePointCity']
                    while ";" in City:
                        c = City[:City.find(";")]
                        old_city_codes.append(c.strip())
                        City = City[City.find(";") + 1:]
                    old_city_codes.append(City[1:].strip())
                else:
                    old_city_codes.append(EP['ExchangePointCity'])
            old_city_codes.sort()

            if new_city_codes != old_city_codes:
                country_cities = {}
                for city_code in new_city_codes:
                    coun_code = Cities.objects.filter(City_code=city_code).values('Country')[0]['Country']
                    if coun_code not in country_cities:
                        country_cities[coun_code] = []
                    country_cities[coun_code].append(city_code)

                if list(country_cities.keys()) != new_country_codes:
                    error = "Ошибка при сопоставлении стран и городов"
                    return render(request, 'testsite/settings_general_exchange_structure_2.html',
                                  {'form': form, 'title': 'Орг. структура обменника', 'param': 2, 'param2':1,
                                   'error': error, 'exch_name': ExchangeName})
                else:

                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                    for country in country_cities.keys():
                        #print(pcc_name.PCCNTR_code)
                        #print(ExchangeName)
                        #print(country)
                        EP_info = PCCNTR_ExchP.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName,
                                                           ExchangePointCountry=country)
                        EP_employees = Users_PCCNTR.objects.filter(ExchangePointID=EP_info.ExchangePointID,
                                                                   ContactType__in=job_positions).values('TG_Contact',
                                                                                                         'CITY').order_by(
                            'TG_Contact')
                        for employee in EP_employees:
                            employee_cities = []
                            if ';' in employee['CITY']:
                                City = employee['CITY']
                                while ";" in City:
                                    c = City[:City.find(";")]
                                    employee_cities.append(c.strip())
                                    City = City[City.find(";") + 1:]
                                employee_cities.append(City[1:].strip())
                            else:
                                employee_cities.append(employee['CITY'])
                            if employee_cities not in new_city_codes:
                                closed_cities = list(set(employee_cities) - set(new_city_codes))
                                closed_city_names = Cities.objects.filter(City_code__in=closed_cities).values_list('Name_RUS', flat=True)
                                closed_city_names = ', '.join(closed_city_names)
                                error = 'По городу ' + closed_city_names + " найдены действующие сотрудники. Необходимо уволить всех сотрудников перед удалением обменника."
                                return render(request, 'testsite/settings_general_exchange_structure_2.html',
                                              {'form': form, 'title': 'Орг. структура обменника', 'param': 2, 'param2':1,
                                               'error': error, 'exch_name': ExchangeName})

                        cities = ''
                        country_cities[country].sort()
                        if len(country_cities[country]) == 1:
                            cities = str(country_cities[country][0])
                        else:
                            for city in country_cities[country]:
                                cities += str(city) + '; '
                            cities = cities[:len(cities) - 2].strip()
                        if EP_info.ExchangePointCity != cities:
                            EP_info.ExchangePointCity = cities
                            EP_info.save()

            if exch_OfficeCourier != ExchangePoints[0]['ExchangePointOfficeCourier']:
                job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                new_job_pos = []
                ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values(
                    'ExchangePointID', 'ExchangePointName', 'ExchangePointCity', 'ExchangePointCountry',
                    'ExchangePointOfficeCourier').order_by('ExchangePointID')
                if len(form.cleaned_data.get('ExchPOfficeCourier')) == 1:
                    #print(form.cleaned_data.get('ExchPOfficeCourier'))
                    #print(form.cleaned_data.get('ExchPOfficeCourier')[0] == 'Офис')
                    if form.cleaned_data.get('ExchPOfficeCourier')[0] == 'Офис':
                        job_pos = 'Куратор'
                    else:
                        job_pos = 'Курьер'
                    jp_info = ContactType.objects.filter(Name_RUS=job_pos).values('ContactType_code')
                    new_job_pos.append(str(jp_info[0]['ContactType_code']))

                    for EP in ExchangePoints:
                        EP_info = PCCNTR_ExchP.objects.get(ExchangePointID=EP['ExchangePointID'])
                        EP_info.ExchangePointOfficeCourier = exch_OfficeCourier
                        EP_info.save()
                        EP_employees = Users_PCCNTR.objects.filter(ExchangePointID=EP['ExchangePointID'],
                                                                   ContactType__in=job_positions).values_list(
                            'TG_Contact', flat=True).order_by('TG_Contact')
                        for employee in EP_employees:
                            EP_employee = Users_PCCNTR.objects.get(TG_Contact=employee, ContactType__in=job_positions)
                            #print(EP_employee.TG_Contact)
                            #print(EP_employee.ContactType)
                            #print(new_job_pos[0])
                            #print(EP_employee.ContactType != new_job_pos[0])
                            if EP_employee.ContactType != new_job_pos[0]:
                                EP_employee.ContactType = new_job_pos[0]
                                EP_employee.save()
                else:
                    for EP in ExchangePoints:
                        EP_info = PCCNTR_ExchP.objects.get(ExchangePointID=EP['ExchangePointID'])
                        EP_info.ExchangePointOfficeCourier = exch_OfficeCourier
                        EP_info.save()

            if form.cleaned_data.get('ExchPName') != ExchangePoints[0]['ExchangePointName']:
                check_exchange_point_name = PCCNTR_ExchP.objects.filter(
                    ExchangePointName=form.cleaned_data.get('ExchPName')).values_list('ExchangePointID', flat=True)
                if len(check_exchange_point_name) == 0:
                    ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values(
                        'ExchangePointID', 'ExchangePointName', 'ExchangePointCity', 'ExchangePointCountry',
                        'ExchangePointOfficeCourier').order_by('ExchangePointID')
                    for EP in ExchangePoints:
                        EP_info = PCCNTR_ExchP.objects.get(ExchangePointID=EP['ExchangePointID'])
                        EP_info.ExchangePointName = form.cleaned_data.get('ExchPName')
                        EP_info.save()
                    ExchangeName = form.cleaned_data.get('ExchPName')
                else:
                    error = 'Обменник с таким наименованием уже зарегистрирован в системе'
                    return render(request, 'testsite/settings_general_exchange_structure_2.html',
                                  {'form': form, 'title': 'Орг. структура обменника', 'param': 2, 'error': error, 'param2':1,
                                   'exch_name': ExchangeName})

            return redirect('general_settings_change_exchange_structure', ExchangeName)


    else:
        ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values('ExchangePointCountry',
                                                                                            'ExchangePointCity',
                                                                                            'ExchangePointName',
                                                                                            'ExchangePointOfficeCourier')
        countries = []
        cities = []
        offcour = []

        for EP in ExchangePoints:
            Country = EP['ExchangePointCountry']
            City = EP['ExchangePointCity']
            officeCourier = EP['ExchangePointOfficeCourier']

            countries.append(Countries.objects.filter(Country_code=Country).values('Name_RUS')[0]['Name_RUS'])
            if '; ' in City:
                while ";" in City:
                    c = City[:City.find(";")]
                    cities.append(Cities.objects.filter(City_code=c.strip()).values('Name_RUS')[0]['Name_RUS'])
                    City = City[City.find(";") + 1:]
                cities.append(Cities.objects.filter(City_code=City[1:].strip()).values('Name_RUS')[0]['Name_RUS'])
            else:
                cities.append(Cities.objects.filter(City_code=City.strip()).values('Name_RUS')[0]['Name_RUS'])

            if '; ' in officeCourier:
                if len(offcour) == 0:
                    offcour = ['Курьер', 'Офис']
            else:
                if len(offcour) == 0:
                    offcour.append(officeCourier)

        ExchPCountry = countries
        ExchPCity = cities
        ExchPName = ExchangeName
        ExchPOfficeCourier = offcour

        form = ExchPInformation(initial={'ExchPCountry': ExchPCountry, 'ExchPCity': ExchPCity, 'ExchPName': ExchPName,
                                         'ExchPOfficeCourier': ExchPOfficeCourier})
    return render(request, 'testsite/settings_general_exchange_structure_2.html',
                  {'form': form, 'title': 'Орг. структура обменника', 'param': 2, 'error': "", 'param2':1,
                   'exch_name': ExchangeName})

#
def general_settings_change_exchange_structure_3_menu(request):
    # global user_type, ExchangeName, exchange_name
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=
    ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']).values(
        'TG_Contact', 'PCCNTR', 'ContactType', 'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат
    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
    ExchangePoint = list(
        PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName).values_list(
            'ExchangePointID', flat=True))
    EP_employee = Users_PCCNTR.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID__in=ExchangePoint,
                                              ContactType__in=job_positions).values('TG_Contact', 'COUNTRY',
                                                                                    'CITY').order_by('TG_Contact')
    location = []
    employee_data = {}
    for employee in EP_employee:
        if ';' in employee['CITY']:
            cities = employee['CITY'].split('; ')
            cities = list(Cities.objects.filter(City_code__in=cities).values_list('Name_RUS', flat=True))
            cities.sort()
            city_name ='(' +  ', '.join(cities) + ')'
        else:
            cities = [employee['CITY']]
            cities = list(Cities.objects.filter(City_code__in=cities).values_list('Name_RUS', flat=True))
            city_name = ', '.join(cities)

        employee_data[employee['TG_Contact']] = {
            'TG_Contact': employee['TG_Contact'],
            'Location': str(Countries.objects.filter(Country_code=employee['COUNTRY']).values('Name_RUS')[0]['Name_RUS']) + ', ' +city_name
        }
        if str(Countries.objects.filter(Country_code=employee['COUNTRY']).values('Name_RUS')[0]['Name_RUS']) + ', ' + city_name not in location:
            location.append(str(Countries.objects.filter(Country_code=employee['COUNTRY']).values('Name_RUS')[0]['Name_RUS']) + ', ' + city_name)

    location = list(set(location))
    location.sort()
    # exchange_name = ExchangeName
    #print(employee_data)


    return render(request, 'testsite/settings_general_change_exchange_structure_3_menu.html',
                  {'title': 'Управление персоналом обменника', 'exch_name': ExchangeName, 'EP_employee': employee_data,
                   'Locations': location})

#
def general_settings_change_exchange_structure_3_employee(request, employee_name):  # НЕ МЕНЯЕТСЯ ВРЕМЯ РАБОТЫ
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    job_positions = ['COUR', 'CUR', 'COUR; CUR', 'CUR; COUR']
    num = Users_PCCNTR.objects.get(TG_Contact=employee_name, ContactType__in=job_positions).pk
    if request.method == 'POST':
        form = ChooseUserforExchP_without_name(request.user, ExchangeName, request.POST)
        if form.is_valid():
            # print(request.POST)
            username = request.user
            pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
            pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

            print(form.cleaned_data['ExchPCities'])
            city = '; '.join(list(Cities.objects.filter(Name_RUS__in=form.cleaned_data['ExchPCities']).values_list('City_code', flat=True)))
            country = Countries.objects.filter(Name_RUS=form.cleaned_data['ExchPCountries']).values_list('Country_code',
                                                                                                         flat=True)[0]

            job_position = ''
            for j_p in form.cleaned_data.get('ExchPOfficeCourier'):
                jp_info = ContactType.objects.filter(Name_RUS=j_p).values('ContactType_code')
                job_position += str(jp_info[0]['ContactType_code']) + "; "
            job_position = job_position[:len(job_position) - 2]

            Employee = Users_PCCNTR.objects.get(PCCNTR=pcc_name.PCCNTR_code, TG_Contact=employee_name,
                                                ContactType__in=job_positions)

            # print(form.cleaned_data['ExchPCities'])
            if str(city) != Employee.CITY:
                Employee.CITY = str(city)

            if str(country) != Employee.COUNTRY:
                Employee.COUNTRY = str(country)
                EP = PCCNTR_ExchP.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName,
                                              ExchangePointCountry=country)
                Employee.ExchangePointID = EP.ExchangePointID

            if job_position != Employee.ContactType:
                Employee.ContactType = str(job_position)

            if form.cleaned_data.get("Mon") != Employee.Monday:
                Employee.Monday = form.cleaned_data.get("Mon")

            if form.cleaned_data.get("Tue") != Employee.Tuesday:
                Employee.Tuesday = form.cleaned_data.get("Tue")

            if form.cleaned_data.get("Wed") != Employee.Wednesday:
                Employee.Wednesday = form.cleaned_data.get("Wed")

            if form.cleaned_data.get("Thu") != Employee.Thursday:
                Employee.Thursday = form.cleaned_data.get("Thu")

            if form.cleaned_data.get("Fri") != Employee.Friday:
                Employee.Friday = form.cleaned_data.get("Fri")

            if form.cleaned_data.get("Sat") != Employee.Saturday:
                Employee.Saturday = form.cleaned_data.get("Sat")

            if form.cleaned_data.get("Sun") != Employee.Sunday:
                Employee.Sunday = form.cleaned_data.get("Sun")

            if form.cleaned_data.get('Mon') or form.cleaned_data.get('Tue') or form.cleaned_data.get(
                    'Wed') or form.cleaned_data.get('Thu') or form.cleaned_data.get('Fri'):
                if int(str(form.cleaned_data.get('Working_hours_Open_Working_days'))[:2]) < int(
                        str(form.cleaned_data.get('Working_hours_Close_Working_days'))[:2]):
                    Opening_hours_workdays = str('c ' + str(
                        form.cleaned_data.get('Working_hours_Open_Working_days') + " до " + str(
                            form.cleaned_data.get('Working_hours_Close_Working_days'))))
                else:
                    error = "Установлено неправильное время работы в будние дни"
                    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                                  {'form': form, 'title': 'Редактирование сотрудника обменника', 'param': 2,
                                   'error': error, 'num': num,
                                   'employee_name': employee_name, 'exch_name': ExchangeName})
            else:
                Opening_hours_workdays = ""

            if form.cleaned_data.get('Sat') or form.cleaned_data.get('Sun'):
                if int(str(form.cleaned_data.get('Working_hours_Open_Weekends'))[:2]) < int(
                        str(form.cleaned_data.get('Working_hours_Close_Weekends'))[:2]):
                    Opening_hours_weekends = str('c ' + str(
                        form.cleaned_data.get('Working_hours_Open_Weekends') + " до " + str(
                            form.cleaned_data.get('Working_hours_Close_Weekends'))))
                else:
                    error = "Установлено неправильное время работы в выходные дни"
                    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                                  {'form': form, 'title': 'Редактирование сотрудника обменника', 'param': 2,
                                   'error': error, "num": num,
                                   'employee_name': employee_name, 'exch_name': ExchangeName})
            else:
                Opening_hours_weekends = ""

            if form.cleaned_data.get('Mon') == False and form.cleaned_data.get('Tue') == False and form.cleaned_data.get(
                    'Wed') == False and form.cleaned_data.get('Thu') == False and form.cleaned_data.get('Fri') == False and form.cleaned_data.get('Sat') == False and form.cleaned_data.get('Sun') == False:
                error = "Не выбраны дни работы сотрудника"
                return render(request, 'testsite/settings_general_exchange_structure_3.html',
                              {'form': form, 'title': 'Редактирование сотрудника обменника', 'param': 2,
                               'error': error, "num": num,
                               'employee_name': employee_name, 'exch_name': ExchangeName})


            # print(Opening_hours_workdays + ' | ' + Employee.ExchangePointOpenHours_Workingdays)
            # print(Opening_hours_weekends + ' | ' + Employee.ExchangePointOpenHours_Weekends)
            if Opening_hours_workdays != Employee.ExchangePointOpenHours_Workingdays:
                Employee.ExchangePointOpenHours_Workingdays = Opening_hours_workdays

            if Opening_hours_weekends != Employee.ExchangePointOpenHours_Weekends:
                Employee.ExchangePointOpenHours_Weekends = Opening_hours_weekends

            if form.cleaned_data.get("ExchPAddress") != Employee.ExchangePointAddress:
                Employee.ExchangePointAddress = form.cleaned_data.get("ExchPAddress")

            Employee.save()
            return redirect('general_settings_change_exchange_structure_3_menu')
    else:
        username = request.user  # ИСПРАВИТЬ ФОРМИРОВАНИЕ СПИСКА
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=
        ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']).values(
            'TG_Contact', 'PCCNTR', 'ContactType', 'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат
        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        ExchangePoint = list(
            PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName).values_list(
                'ExchangePointID', flat=True))
        EP_employee = Users_PCCNTR.objects.get(TG_Contact=employee_name, PCCNTR=pcc_name.PCCNTR_code,
                                               ExchangePointID__in=ExchangePoint, ContactType__in=job_positions)
        exchp_offcour = []

        if '; ' in EP_employee.ContactType:
            exchp_offcour = ['Курьер', 'Куратор']
        else:
            exchp_offcour.append(
                ContactType.objects.filter(ContactType_code=EP_employee.ContactType).values('Name_RUS')[0]['Name_RUS'])

        if EP_employee.ExchangePointOpenHours_Workingdays != '':
            OpenHours_Workingdays = str(EP_employee.ExchangePointOpenHours_Workingdays)
            open_hours_workdays = OpenHours_Workingdays[
                                  OpenHours_Workingdays.find('с') + 3:OpenHours_Workingdays.find('д') - 1].strip()
            close_hours_workdays = OpenHours_Workingdays[OpenHours_Workingdays.find('д') + 3:].strip()
        else:
            open_hours_workdays = ''
            close_hours_workdays = ''

        if EP_employee.ExchangePointOpenHours_Weekends != '':
            OpenHours_Weekends = str(EP_employee.ExchangePointOpenHours_Weekends)
            open_hours_weekends = OpenHours_Weekends[
                                  OpenHours_Weekends.find('с') + 3:OpenHours_Weekends.find('д') - 1].strip()
            close_hours_weekends = OpenHours_Weekends[OpenHours_Weekends.find('д') + 3:].strip()
        else:
            open_hours_weekends = ''
            close_hours_weekends = ''

        if ';' in EP_employee.CITY:
            cities = EP_employee.CITY.split('; ')
            cities = list(Cities.objects.filter(City_code__in=cities).values_list('Name_RUS', flat=True))
        else:
            cities = [EP_employee.CITY]
            cities = list(Cities.objects.filter(City_code__in=cities).values_list('Name_RUS', flat=True))

        # print(cities)

        form = ChooseUserforExchP_without_name(request.user, ExchangeName, {
            'ExchPCountries': Countries.objects.filter(Country_code=EP_employee.COUNTRY).values('Name_RUS')[0][
                'Name_RUS']
            , 'ExchPCities': cities
            , 'ExchPOfficeCourier': exchp_offcour
            , 'Mon': EP_employee.Monday, 'Tue': EP_employee.Tuesday, 'Wed': EP_employee.Wednesday,
            'Thu': EP_employee.Thursday
            , 'Fri': EP_employee.Friday, 'Sat': EP_employee.Saturday, 'Sun': EP_employee.Sunday
            , 'Working_hours_Open_Working_days': open_hours_workdays,
            'Working_hours_Close_Working_days': close_hours_workdays
            , 'Working_hours_Open_Weekends': open_hours_weekends, 'Working_hours_Close_Weekends': close_hours_weekends
            , 'ExchPAddress': EP_employee.ExchangePointAddress})

    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                  {'form': form, 'title': 'Редактирование сотрудника обменника', 'param': 2, 'error': "",
                   'employee_name': employee_name, 'exch_name': ExchangeName, "num": num})

#
def general_settings_change_exchange_structure_3_delete_employee(request, employee_name):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    job_positions = ['COUR', 'CUR', 'COUR; CUR', 'CUR; COUR']
    num = Users_PCCNTR.objects.get(TG_Contact=employee_name, ContactType__in=job_positions).pk
    return render(request, 'testsite/settings_general_change_exchange_structure_3_delete_employee.html',
                  {'title': 'Увольнение сотрудника обменника', 'employee_name': employee_name,"num": num})

#
def general_settings_change_exchange_structure_3_delete_employee_final(request, employee_name):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

    job_positions = ['COUR', 'CUR', 'COUR; CUR', 'CUR; COUR']
    ExchangePoint = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=ExchangeName).values(
        'ExchangePointID', 'ExchangePointCountry')
    for EP in ExchangePoint:
        user = Users_PCCNTR.objects.filter(TG_Contact=employee_name, ContactType__in=job_positions,
                                           COUNTRY=EP['ExchangePointCountry'])
        if len(user) == 1:
            user.delete()
    return redirect('general_settings_change_exchange_structure_3_menu')

#
def general_settings_exchange_structure_new_1(request):
    # global checked_username, user_type, pcc_code
    user_type = cache.get('user_type')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType=
    ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']).values(
        'TG_Contact', 'PCCNTR', 'ContactType', 'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    pcc_code = pcc_name.PCCNTR_code
    cache.set('pcc_code', pcc_code)
    Exchangedata = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_code)
    if len(Exchangedata) == 0:
        param2 = 0
    else:
        param2 = 1
    if request.method == 'POST':
        form = ChooseOrgforExchP(data=request.POST)
        if form.is_valid():
            username = request.user
            find_user = Users.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'))
            if len(find_user) != 0:
                find_user_1 = Users_PCCNTR.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'), ContactType=
                ContactType.objects.filter(Name_RUS='Партнер').values('ContactType_code')[0]['ContactType_code'])
                if len(find_user_1) == 0 or (form.cleaned_data.get('UserToCheck') != username):
                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                    find_user_2 = Users_PCCNTR.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'), ContactType__in=job_positions)
                    find_user_3 = Users_PCCNTR.objects.filter(TG_Contact=form.cleaned_data.get('UserToCheck'), ContactType=ContactType.objects.filter(Name_RUS='Организатор').values('ContactType_code')[0]['ContactType_code'])
                    if len(find_user_2) == 0 or (form.cleaned_data.get('UserToCheck') != username) or len(find_user_3) != 0:
                        checked_username = form.cleaned_data.get('UserToCheck')
                        cache.set('checked_username', checked_username)
                        return redirect('general_settings_exchange_structure_new_1_confirm', 1)
                    else:
                        error = 'Данный пользователь зарегистрирован в системе как "Сотрудник обменника"'
                        return render(request, 'testsite/settings_general_exchange_structure_1.html',
                                      {'form': form, 'title': 'Выбор организатора для обменника', 'param': 1, 'param2': param2,
                                       'error': error})
                else:
                    error = 'Данный пользователь зарегистрирован в системе как "Партнер"'
                    return render(request, 'testsite/settings_general_exchange_structure_1.html',
                                  {'form': form, 'title': 'Выбор организатора для обменника', 'param': 1, 'param2': param2,
                                   'error': error})
            else:
                error = 'Данный пользователь не зарегистрирован в системе как "Клиент"'
                return render(request, 'testsite/settings_general_exchange_structure_1.html',
                              {'form': form, 'title': 'Выбор организатора для обменника', 'param': 1, 'param2': param2, 'error': error})

    else:
        form = ChooseOrgforExchP()
    return render(request, 'testsite/settings_general_exchange_structure_1.html',
                  {'form': form, 'title': 'Выбор организатора для обменника', 'param': 1, 'param2': param2, 'error': ""})

#
def general_settings_exchange_structure_new_1_confirm(request, num):
    # global checked_username, code_check, user_type
    # user_type = cache.get('user_type')
    checked_username = cache.get('checked_username')
    if num != 1 and num != 4:
        user = User.objects.get(username=checked_username)
        user_email = user.email
        code_check = randint(10000, 99999)
        cache.set('code_check', code_check)
        mail_subject = 'Код для подтверждения регистрации пользователя как "Организатор"'
        reason = 'регистрации пользователя как "Организатор"'
        message = render_to_string('testsite/acc_active_email.html', {
            'user': user,
            'reason': reason,
            'code': code_check,
        })
        to_email = user_email
        send_mail(mail_subject, message, "ya.maxrov@ya.ru", [to_email], fail_silently=False, )
        return redirect('email_confirm', num * 2)

    else:
        return render(request, 'testsite/settings_general_exchange_structure_1_confirm.html',
                      {'title': 'Подтверждение выбора организатора для обменника', 'username': checked_username,
                       'param': num})

#
def general_settings_exchange_structure_new_1_final(request):
    # global checked_username, user_type
    # user_type = cache.get('user_type')
    checked_username = cache.get('checked_username')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    chosen_user = Users.objects.get(TG_Contact=checked_username)
    contacttype_pccntr = ContactType.objects.filter(Name_RUS="Организатор").values('ContactType_code')
    Users_PCCNTR.objects.create(TG_Contact=checked_username, ContactType=contacttype_pccntr[0]['ContactType_code'],
                                COUNTRY=chosen_user.COUNTRY, CITY=chosen_user.CITY,
                                Language=chosen_user.Language, PCCNTR=pcc_name.PCCNTR_code)
    return redirect('general_settings_exchange_structure_new_2')

#
def general_settings_exchange_structure_new_2(request):
    # global user_type, checked_username, exchange_name, pcc_code
    user_type = cache.get('user_type')
    checked_username = cache.get('checked_username')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    pcc_code = pcc_name.PCCNTR_code
    cache.set('pcc_code', pcc_code)
    Exchangedata = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_code)
    if len(Exchangedata) == 0:
        param2 = 0
    else:
        param2 = 1
    if request.method == 'POST':
        form = ExchPInformation(data=request.POST)
        if form.is_valid():
            exch_point_IDs = ''
            exch_point_IDs_list = []
            exch_OfficeCourier = str("; ".join(form.cleaned_data.get('ExchPOfficeCourier')))
            check_exchange_point_name = PCCNTR_ExchP.objects.filter(
                ExchangePointName=form.cleaned_data.get('ExchPName')).values_list('ExchangePointID', flat=True)
            if len(check_exchange_point_name) == 0:
                for country in form.cleaned_data.get('ExchPCountry'):
                    cities = ''
                    coun_code = Countries.objects.filter(Name_RUS=country).values('Country_code')[0]['Country_code']
                    count_ExchangePoint = PCCNTR_ExchP.objects.filter(
                        ExchangePointCountry=coun_code).values_list('ExchangePointID', flat=True).order_by(
                        'ExchangePointID')
                    if len(count_ExchangePoint) == 0:
                        quantity_EP = '1'
                    else:
                        last_exchP = count_ExchangePoint[len(count_ExchangePoint) - 1]
                        quantity_EP = str(int(last_exchP[5:]) + 1)

                    ExchPID = str('EP_' + str(coun_code) + quantity_EP.zfill(4))
                    exch_point_IDs_list.append(ExchPID)
                    exch_point_IDs += str(ExchPID) + '; '
                    for city in form.cleaned_data.get('ExchPCity'):
                        city_info = Cities.objects.filter(Name_RUS=city).values('City_code', 'Country')
                        if city_info[0]['Country'] == coun_code:
                            cities += str(str(city_info[0]['City_code']) + "; ")
                    cities = cities[:len(cities) - 2]
                    PCCNTR_ExchP.objects.create(ExchangePointID=ExchPID, PCCNTR=pcc_name.PCCNTR_code,
                                                ExchangePointCountry=coun_code, ExchangePointCity=cities,
                                                ExchangePointName=form.cleaned_data.get('ExchPName'),
                                                ExchangePointOfficeCourier=exch_OfficeCourier)
                if len(exch_point_IDs_list) == 1:
                    exch_point_IDs = exch_point_IDs[:len(exch_point_IDs) - 2]
                else:
                    exch_point_IDs_list.sort()
                    exch_point_IDs = str("; ".join(exch_point_IDs_list))
                pks = list(Users_PCCNTR.objects.filter(TG_Contact=checked_username, ContactType='ORG').values_list('pk',
                                                                                                                   flat=True))
                organizator = Users_PCCNTR.objects.get(TG_Contact=checked_username, pk=pks[len(pks) - 1])
                organizator.ExchangePointID = exch_point_IDs
                organizator.save()
                exchange_name = form.cleaned_data.get('ExchPName')
                cache.set('ExchangeName', exchange_name)
                return redirect('general_settings_exchange_structure_new_3', 1)
            else:
                error = 'Обменник с таким наименованием уже зарегистрирован в системе'
                return render(request, 'testsite/settings_general_exchange_structure_2.html',
                              {'form': form, 'title': 'Орг. структура обменника', 'param': 1, 'param2': param2, 'error': error})
    else:
        form = ExchPInformation()
    return render(request, 'testsite/settings_general_exchange_structure_2.html',
                  {'form': form, 'title': 'Орг. структура обменника', 'param': 1, 'param2': param2, 'error': ""})

#
def general_settings_exchange_structure_new_3(request, num):
    # global checked_username, user_type, employee_data, exchange_name, param
    # user_type = cache.get('user_type')
    # checked_username = cache.get('checked_username')
    exchange_name = cache.get('ExchangeName')
    param = num
    cache.set('param', param)
    if request.method == 'POST':
        form = ChooseUserforExchP(request.user, exchange_name, request.POST)
        if form.is_valid():
            username = request.user
            pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
            pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

            checked_username = form.cleaned_data['chosen_user']

            chosen_user = User.objects.filter(username=checked_username)
            if len(chosen_user) == 0:
                error = "Пользователь " + str(checked_username) + " не зарегистрирован в системе"
                return render(request, 'testsite/settings_general_exchange_structure_3.html',
                              {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': error, 'num':num})

            job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
            employees = Users_PCCNTR.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ContactType__in=job_positions).values_list('TG_Contact', flat=True)
            if checked_username in employees:
                empl_exchpoint = Users_PCCNTR.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ContactType__in=job_positions, TG_Contact=checked_username).values_list('ExchangePointID', flat=True)[0]
                exch_name = PCCNTR_ExchP.objects.filter(ExchangePointID=empl_exchpoint).values_list('ExchangePointName', flat=True)[0]
                error = "Пользователь " + str(checked_username) + " уже зарегистрирован как сотрудник обменника " + str(exch_name)
                return render(request, 'testsite/settings_general_exchange_structure_3.html',
                              {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': error, 'num':num})

            city = Cities.objects.filter(Name_RUS=form.cleaned_data['ExchPCities']).values_list('City_code', flat=True)[0]
            country = Countries.objects.filter(Name_RUS=form.cleaned_data['ExchPCountries']).values_list('Country_code',
                                                                                                         flat=True)[0]
            Exchange_PointID = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointCountry=country,ExchangePointName=exchange_name).values_list('ExchangePointID', flat=True)[0]

            job_positions = []
            for job_position in form.cleaned_data.get('ExchPOfficeCourier'):
                jp_info = ContactType.objects.filter(Name_RUS=job_position).values('ContactType_code')
                job_positions.append(jp_info[0]['ContactType_code'])

            if form.cleaned_data.get('Mon') or form.cleaned_data.get('Tue') or form.cleaned_data.get(
                    'Wed') or form.cleaned_data.get('Thu') or form.cleaned_data.get('Fri'):
                if int(str(form.cleaned_data.get('Working_hours_Open_Working_days'))[:2]) < int(
                        str(form.cleaned_data.get('Working_hours_Close_Working_days'))[:2]):
                    Opening_hours_workdays = str('c ' + str(
                        form.cleaned_data.get('Working_hours_Open_Working_days') + " до " + str(
                            form.cleaned_data.get('Working_hours_Close_Working_days'))))
                else:
                    error = "Установлено неправильное время работы в будние дни"
                    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                                  {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': error, 'num':num})
            else:
                Opening_hours_workdays = ""

            if form.cleaned_data.get('Sat') or form.cleaned_data.get('Sun'):
                if int(str(form.cleaned_data.get('Working_hours_Open_Weekends'))[:2]) < int(
                        str(form.cleaned_data.get('Working_hours_Close_Weekends'))[:2]):
                    Opening_hours_weekends = str('c ' + str(
                        form.cleaned_data.get('Working_hours_Open_Weekends') + " до " + str(
                            form.cleaned_data.get('Working_hours_Close_Weekends'))))
                else:
                    error = "Установлено неправильное время работы в выходные дни"
                    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                                  {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': error})
            else:
                Opening_hours_weekends = ""

            if (form.cleaned_data.get('Mon') == False and form.cleaned_data.get('Tue') == False and
                    form.cleaned_data.get('Wed') == False and form.cleaned_data.get('Thu') == False and
                    form.cleaned_data.get('Fri') == False and form.cleaned_data.get('Sat') == False and
                    form.cleaned_data.get('Sun') == False):
                error = "Не выбраны дни работы сотрудника"
                return render(request, 'testsite/settings_general_exchange_structure_3.html',
                                  {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': error, 'num':num})

            employee_data = {'TG_Contact': checked_username, 'ExchangePointID': Exchange_PointID,'PCCNTR': pcc_name.PCCNTR_code
                , 'ContactType': job_positions, 'Country': country, 'City': city, 'Monday': form.cleaned_data.get('Mon')
                , 'Tuesday': form.cleaned_data.get('Tue'), 'Wednesday': form.cleaned_data.get('Wed')
                , 'Thursday': form.cleaned_data.get('Thu'), 'Friday': form.cleaned_data.get('Fri')
                , 'Saturday': form.cleaned_data.get('Sat'), 'Sunday': form.cleaned_data.get('Sat')
                , 'ExchangePointOpenHours_Workingdays': Opening_hours_workdays
                , 'ExchangePointOpenHours_Weekends': Opening_hours_weekends
                , 'ExchangePointAddress': form.cleaned_data.get('ExchPAddress')}
            cache.set('employee_data', employee_data)
            return redirect('general_settings_exchange_structure_new_3_confirm', 1)
    else:
        form = ChooseUserforExchP(request.user, exchange_name)
    return render(request, 'testsite/settings_general_exchange_structure_3.html',
                  {'form': form, 'title': 'Сотрудники обменника', 'param': 1, 'error': "", 'num':num})

#
def general_settings_exchange_structure_new_3_confirm(request, num):
    # global checked_username, code_check, employee_data, user_type, exchange_name
    # user_type = cache.get('user_type')
    checked_username = cache.get('checked_username')
    # exchange_name = cache.get('ExchangeName')
    if num == 2:
        user = User.objects.get(username=checked_username)
        user_email = user.email
        code_check = randint(10000, 99999)
        cache.set('code_check', code_check)
        mail_subject = 'Код для подтверждения регистрации пользователя как сотрудника обменника'
        reason = 'регистрации пользователя как сотрудника обменника'
        message = render_to_string('testsite/acc_active_email.html', {
            'user': user,
            'reason': reason,
            'code': code_check,
        })
        to_email = user_email
        send_mail(mail_subject, message, "ya.maxrov@ya.ru", [to_email], fail_silently=False, )
        return redirect('email_confirm', 5)
    else:
        return render(request, 'testsite/settings_general_exchange_structure_3_confirm.html',
                      {'title': 'Подтверждение выбора сотрудника для обменника', 'username': checked_username})

#
def general_settings_exchange_structure_new_3_final(request):
    # global checked_username, employee_data, user_type, exchange_name, param
    # user_type = cache.get('user_type')
    checked_username = cache.get('checked_username')
    # exchange_name = cache.get('ExchangeName')
    employee_data = cache.get('employee_data')
    param = cache.get('param')
    chosen_user = Users.objects.get(TG_Contact=checked_username)
    if len(employee_data['ContactType']) == 1:
        contact_type = str(employee_data['ContactType'][0])
    else:
        contact_type = str(employee_data['ContactType'][0]) + "; " + str(employee_data['ContactType'][1])
    Users_PCCNTR.objects.create(TG_Contact=checked_username, ExchangePointID=employee_data['ExchangePointID']
                                , ContactType=contact_type, COUNTRY=employee_data['Country'], CITY=employee_data['City']
                                , Monday=employee_data['Monday'], Tuesday=employee_data['Tuesday']
                                , Wednesday=employee_data['Wednesday'], Thursday=employee_data['Thursday']
                                , Friday=employee_data['Friday'], Saturday=employee_data['Saturday']
                                , Sunday=employee_data['Sunday']
                                , ExchangePointOpenHours_Workingdays=employee_data['ExchangePointOpenHours_Workingdays']
                                , ExchangePointOpenHours_Weekends=employee_data['ExchangePointOpenHours_Weekends']
                                , ExchangePointAddress=employee_data['ExchangePointAddress']
                                , Language=chosen_user.Language, PCCNTR=employee_data['PCCNTR'])
    if param == 1:
        cache.delete('param')
        cache.delete('employee_data')
        return redirect('general_settings_exchange_deals_new')
    else:
        cache.delete('param')
        cache.delete('employee_data')
        return redirect('general_settings_change_exchange_structure_3_menu')

#
def general_settings_exchange_deals_new(request):
    # global user_type, exchange_name
    user_type = cache.get('user_type')
    exch_name = cache.get('ExchangeName')
    exch_code = PCCNTR_ExchP.objects.filter(ExchangePointName=exch_name).values_list('pk', flat=True)[0]
    if request.method == 'POST':
        form = ChooseDealsforExchP(request.user, request.POST)
        if form.is_valid():
            quantity_of_new_opertypes = 0
            username = request.user
            pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
            pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
            pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("OperType",
                                                                                                     flat=True)
            pcc_opertypes = list(set(list(pcc_opertypes)))
            ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=exch_name).values_list('ExchangePointID',
                                                                                                  flat=True).order_by(
                'ExchangePointID')
            for EP in ExchangePoints:
                ExchangePoint = PCCNTR_ExchP.objects.get(ExchangePointID=EP)

                #for deal in form.cleaned_data.get('chosen_deals'):
                p_t_b = ""
                p_t_s = ""
                if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                    p_t_b = "CSH"
                elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                    p_t_b = "CRP"
                elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                    p_t_b = "CRD"

                if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                    p_t_s = "CSH"
                elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                    p_t_s = "CRP"
                elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                    p_t_s = "CRD"

                deal_data = (ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                    SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                    ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy")))
                             .values('pk','Name_RUS', 'OperTypes', 'SendTransferType', 'ReceiveTransferType'))
                # print(deal_data[0]['Name_RUS'])

                deal = str(deal_data[0]['Name_RUS'])
                curr_to = deal[deal.find(">") + 2:]
                curr_to = curr_to[:curr_to.find(" ")]
                if form.cleaned_data.get('Norm_Prib_Name_1_1') == form.cleaned_data.get('Min_amount'):
                    Norm_Prib = str(form.cleaned_data.get('Norm_Prib_Name_1_1')) + "-" + str(
                        form.cleaned_data.get('Norm_Prib_Name_1_2')) + " " + curr_to + ": " + str(
                        form.cleaned_data.get('Norm_Prib_Percent_1')) + "%" + "; "

                    if str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_2_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) + "%" + "; "

                    elif form.cleaned_data.get('Norm_Prib_Name_1_2') != form.cleaned_data.get('Max_amount'):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 0,
                                       "exch_name": exch_name,
                                       'user_type': user_type, 'error': error, 'exch_code':exch_code})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "") and (
                            form.cleaned_data.get('Norm_Prib_Name_1_2') + 1 != form.cleaned_data.get('Norm_Prib_Name_2_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 0,
                                       "exch_name": exch_name,'exch_code':exch_code,
                                       'user_type': user_type, 'error': error})

                    if str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_3_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) + "%" + "; "

                    elif str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "" and float(
                        form.cleaned_data.get('Norm_Prib_Name_2_2')) != float(
                        form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 0,
                                       "exch_name": exch_name,'exch_code':exch_code,
                                       'user_type': user_type, 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) + 1 != float(
                            form.cleaned_data.get('Norm_Prib_Name_3_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 0,
                                       "exch_name": exch_name,'exch_code':exch_code,
                                       'user_type': user_type, 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != float(
                            form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 0,
                                       "exch_name": exch_name,'exch_code':exch_code,
                                       'user_type': user_type, 'error': error})

                else:
                    error = 'Минимальная сумма сделки не совпадает с началом промужутка нормы прибыльности'
                    return render(request, 'testsite/settings_general_exchange_deals.html',
                                  {'form': form, 'title': 'Направления сделок', 'param': 0, "exch_name": exch_name,
                                   'user_type': user_type, 'error': error, 'exch_code':exch_code})

                Norm_Prib = Norm_Prib[:len(Norm_Prib) - 2]

                if str(form.cleaned_data.get('Min_amount')) != "":
                    min_amount = form.cleaned_data.get('Min_amount')
                else:
                    min_amount = -1

                if str(form.cleaned_data.get('Max_amount')) != "":
                    max_amount = form.cleaned_data.get('Max_amount')
                else:
                    max_amount = -1

                EP_ExchangeID.objects.create(PCCNTR=pcc_name.PCCNTR_code,
                                             ExchangePointID=ExchangePoint.ExchangePointID,
                                             ExchangeTransferID=deal_data[0]['pk'],
                                             ExchTOAmount_Min=min_amount, ExchTOAmount_Max=max_amount,
                                             EP_PRFTNORM=Norm_Prib)
                opertypes = deal_data[0]['OperTypes']
                OPRTs = []
                if ';' in opertypes:
                    while ';' in opertypes:
                        oprt = opertypes[:opertypes.find(";")].strip()
                        OPRTs.append(oprt)
                        opertypes = opertypes[opertypes.find(";") + 1:].strip()
                    OPRTs.append(opertypes.strip())
                else:
                    OPRTs.append(opertypes.strip())

                if len(OPRTs) == 2:
                    if OPRTs[0] not in pcc_opertypes:
                        PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[0],
                                                        SendTransferType=deal_data[0]['SendTransferType'],
                                                        ReceiveTransferType='CRP')
                        pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                            "OperType", flat=True)
                        pcc_opertypes = list(set(list(pcc_opertypes)))
                        quantity_of_new_opertypes += 1
                    if OPRTs[1] not in pcc_opertypes:
                        PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[1],
                                                        SendTransferType='CRP',
                                                        ReceiveTransferType=deal_data[0]['ReceiveTransferType'])
                        pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                            "OperType", flat=True)
                        pcc_opertypes = list(set(list(pcc_opertypes)))
                        quantity_of_new_opertypes += 1
                elif OPRTs[0] not in pcc_opertypes:
                        PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[0],
                                                        SendTransferType=deal_data[0]['SendTransferType'],
                                                        ReceiveTransferType=deal_data[0]['ReceiveTransferType'])
                        pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                            "OperType", flat=True)
                        pcc_opertypes = list(set(list(pcc_opertypes)))
                        quantity_of_new_opertypes += 1


            if quantity_of_new_opertypes != 0:
                return redirect('general_settings_exchange_rate_source_new')
            else:
                return redirect('general_settings_exchange_points')
    else:
        form = ChooseDealsforExchP(request.user, initial={'Min_amount': 0, 'Max_amount': 999999})
    return render(request, 'testsite/settings_general_exchange_deals.html',
                  {'form': form, 'title': 'Направления сделок', 'param': 0, "exch_name": exch_name, 'exch_code':exch_code,
                   'user_type': user_type})

#
def general_settings_exchange_deals_add_new(request):
    # global user_type, ExchangeName
    username = request.user
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    exch_code = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('pk', flat=True)[0]
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                          flat=True).order_by(
        'ExchangePointID')
    Deals = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID__in=ExchangePoints).values_list(
        "ExchangeTransferID", flat=True)
    Deals = list(set(list(Deals)))

    Deals_name = ExchangeID.objects.filter(pk__in=Deals).values_list(
        "Name_RUS", flat=True)
    Deals_name = list(set(list(Deals_name)))
    Deals_name.sort()

    if request.method == 'POST':
        form = ChooseDealsforExchP_add(request.user,  request.POST)
        if form.is_valid():
            quantity_of_new_opertypes = 0
            username = request.user
            pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
            pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
            pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("OperType",
                                                                                                     flat=True)
            pcc_opertypes = list(set(list(pcc_opertypes)))
            ExchangePoints = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                                  flat=True).order_by(
                'ExchangePointID')
            p_t_b = ""
            p_t_s = ""
            if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                p_t_b = "CSH"
            elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                p_t_b = "CRP"
            elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                p_t_b = "CRD"

            if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                p_t_s = "CSH"
            elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                p_t_s = "CRP"
            elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                p_t_s = "CRD"

            for EP in ExchangePoints:
                ExchangePoint = PCCNTR_ExchP.objects.get(ExchangePointID=EP)
                deal_data = (ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                      SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                      ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy")))
                             .values('pk', 'Name_RUS', 'OperTypes', 'SendTransferType', 'ReceiveTransferType'))

                deal = str(deal_data[0]['Name_RUS'])
                if deal in Deals_name:
                    error = 'Выбранное направление сделки уже зарегистрировано'
                    return render(request, 'testsite/settings_general_exchange_deals.html',
                                  {'form': form, 'title': 'Направления сделок', 'param': 2,
                                   "exch_name": ExchangeName,'user_type': user_type, 'Deals': Deals_name, 'error': error})

                curr_to = deal[deal.find(">") + 2:]
                curr_to = curr_to[:curr_to.find(" ")]

                if form.cleaned_data.get('Norm_Prib_Name_1_1') == form.cleaned_data.get('Min_amount'):
                    Norm_Prib = str(form.cleaned_data.get('Norm_Prib_Name_1_1')) + "-" + str(
                        form.cleaned_data.get('Norm_Prib_Name_1_2')) + " " + curr_to + ": " + str(
                        form.cleaned_data.get('Norm_Prib_Percent_1')) + "%" + "; "

                    if str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_2_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) + "%" + "; "

                    elif form.cleaned_data.get('Norm_Prib_Name_1_2') != form.cleaned_data.get('Max_amount'):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 2,
                                       "exch_name": ExchangeName,
                                       'user_type': user_type, 'Deals': Deals_name, 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "") and (
                            form.cleaned_data.get('Norm_Prib_Name_1_2') + 1 != form.cleaned_data.get('Norm_Prib_Name_2_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 2,
                                       "exch_name": ExchangeName,
                                       'user_type': user_type, 'Deals': Deals_name, 'error': error})

                    if str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_3_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) + "%" + "; "

                    elif str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "" and float(
                        form.cleaned_data.get('Norm_Prib_Name_2_2')) != float(
                        form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 2,
                                       "exch_name": ExchangeName,
                                       'user_type': user_type, 'Deals': Deals_name, 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) + 1 != float(
                            form.cleaned_data.get('Norm_Prib_Name_3_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 2,
                                       "exch_name": ExchangeName,
                                       'user_type': user_type, 'Deals': Deals_name, 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != float(
                            form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 2,
                                       "exch_name": ExchangeName,
                                       'user_type': user_type, 'Deals': Deals_name, 'error': error})

                else:
                    error = 'Минимальная сумма сделки не совпадает с началом промужутка нормы прибыльности'
                    return render(request, 'testsite/settings_general_exchange_deals.html',
                                  {'form': form, 'title': 'Направления сделок', 'param': 2, "exch_name": ExchangeName,
                                   'user_type': user_type, 'Deals': Deals_name, 'error': error})

                Norm_Prib = Norm_Prib[:len(Norm_Prib) - 2]

                if str(form.cleaned_data.get('Min_amount')) != "":
                    min_amount = form.cleaned_data.get('Min_amount')
                else:
                    min_amount = -1

                if str(form.cleaned_data.get('Max_amount')) != "":
                    max_amount = form.cleaned_data.get('Max_amount')
                else:
                    max_amount = -1

                EP_ExchangeID.objects.create(PCCNTR=pcc_name.PCCNTR_code,
                                             ExchangePointID=ExchangePoint.ExchangePointID,
                                             ExchangeTransferID=deal_data[0]['pk'],
                                             ExchTOAmount_Min=min_amount, ExchTOAmount_Max=max_amount,
                                             EP_PRFTNORM=Norm_Prib)
                opertypes = deal_data[0]['OperTypes']
                OPRTs = []
                if ';' in opertypes:
                    while ';' in opertypes:
                        oprt = opertypes[:opertypes.find(";")].strip()
                        OPRTs.append(oprt)
                        opertypes = opertypes[opertypes.find(";") + 1:].strip()
                    OPRTs.append(opertypes.strip())
                else:
                    OPRTs.append(opertypes.strip())

                if len(OPRTs) == 2:
                    if OPRTs[0] not in pcc_opertypes:
                        PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[0],
                                                        SendTransferType=deal_data[0]['SendTransferType'],
                                                        ReceiveTransferType='CRP')
                        pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                            "OperType", flat=True)
                        pcc_opertypes = list(set(list(pcc_opertypes)))
                        quantity_of_new_opertypes += 1
                    if OPRTs[1] not in pcc_opertypes:
                        PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[1],
                                                        SendTransferType='CRP',
                                                        ReceiveTransferType=deal_data[0]['ReceiveTransferType'])
                        pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                            "OperType", flat=True)
                        pcc_opertypes = list(set(list(pcc_opertypes)))
                        quantity_of_new_opertypes += 1
                elif OPRTs[0] not in pcc_opertypes:
                    PCCNTR_OperTypes.objects.create(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[0],
                                                    SendTransferType=deal_data[0]['SendTransferType'],
                                                    ReceiveTransferType=deal_data[0]['ReceiveTransferType'])
                    pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                        "OperType", flat=True)
                    pcc_opertypes = list(set(list(pcc_opertypes)))
                    quantity_of_new_opertypes += 1

            if quantity_of_new_opertypes != 0:
                return redirect('general_settings_exchange_rate_source_new')
            else:
                return redirect('general_settings_exchange_points')
    else:
        form = ChooseDealsforExchP_add(request.user,  initial={'Min_amount': 0, 'Max_amount': 999999})
    return render(request, 'testsite/settings_general_exchange_deals.html',
                  {'form': form, 'title': 'Направления сделок', 'param': 2, "exch_name": ExchangeName, 'exch_code':exch_code,
                   'user_type': user_type, 'Deals': Deals_name})

#
def general_settings_exchange_rate_source_new(request):
    # global user_type, ExchangeName, exchange_name
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
   
    if "PART" in list(ContactType.objects.filter(Name_RUS=user_type).values_list('ContactType_code', flat=True)):
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        Quotes = QuotesRC.objects.all().values_list('QuotesRC_Code', flat=True)

        Empty_OperTypes = list(PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).exclude(QuotesRC__in=Quotes
                                                                                              ).values_list(
            "OperType", 'QuotesRC').order_by("OperType"))
        # Currency_types = ExchangeID.objects.filter(Name_RUS__in=Empty_OperTypes).values_list("SendTransferType",
        #                                                                                      "ReceiveTransferType").order_by(
        #     "Name_RUS")
    elif "ORG" in list(ContactType.objects.filter(Name_RUS=user_type).values_list('ContactType_code', flat=True)):
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        EPID_str = '; '.join(EPID)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ContactType='ORG', ExchangePointID=EPID_str).values(
            'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        Quotes = QuotesRC.objects.all().values_list('QuotesRC_Code', flat=True)
        Empty_OperTypes = list(PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).exclude(QuotesRC__in=Quotes).values_list(
                                                                                            "OperType", 'QuotesRC').order_by("OperType"))
        # Currency_types = ExchangeID.objects.filter(Name_RUS__in=Empty_OperTypes).values_list("SendTransferType","ReceiveTransferType").order_by("Name_RUS")

    # print(Empty_OperTypes)
    num = len(Empty_OperTypes)

    Opertypes = {}

    for i in range(len(Empty_OperTypes)):
        Opertypes['N_' + str(i)] = Empty_OperTypes[i][0]

    if request.method == 'POST':
        form = ChooseSourceforExchDeals(Empty_OperTypes, request.POST)
        if form.is_valid():
            if num == 1:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1']]
            elif num == 2:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2']]
            elif num == 3:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3']]
            elif num == 4:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3'], ['chosen_quote_4', 'chosen_bank_4']]
            elif num == 5:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3'], ['chosen_quote_4', 'chosen_bank_4'],
                                    ['chosen_quote_5', 'chosen_bank_5']]

            for i in range(len(Used_form_fields)):
                Opertype = PCCNTR_OperTypes.objects.get(PCCNTR=pcc_name.PCCNTR_code, OperType=Empty_OperTypes[i][0])
                Opertype.QuotesRC = QuotesRC.objects.filter(Name_RUS=form.cleaned_data.get(Used_form_fields[i][0])).values('QuotesRC_Code')[0]['QuotesRC_Code']
                # Opertype.Bank = '-'   #  form.cleaned_data.get(Used_form_fields[i][1])
                Opertype.save()

            return redirect('general_settings_exchange_points')

    else:
        form = ChooseSourceforExchDeals(Empty_OperTypes)
    return render(request, 'testsite/settings_general_exchange_rate_source.html',
                  {'form': form, 'title': 'Источники курсов валют', 'Opertypes': Opertypes, 'num': num, 'param': 0, 'exch_name': ExchangeName})

#
def general_settings_change_exchange_deals_1(request):
    # global user_type, chosen_ep_deals, EP_Deals, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    EP_Deals = cache.get('EP_Deals')
    # username = request.user
    usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
        'ContactType_code']
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "PART":
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user).values('TG_Contact', 'ContactType', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "ORG":
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        EPID_str = '; '.join(EPID)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ContactType='ORG', ExchangePointID=EPID_str).values(
            'TG_Contact', 'ContactType',
            'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    if request.method == 'POST':
        form = ChooseExchangePointsandDeals(request.user, usertype, ExchangeName, request.POST)
        # min = []
        # max = []
        # norm_prib = []
        if form.is_valid():
            p_t_b = ""
            p_t_s = ""
            if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                p_t_b = "CSH"
            elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                p_t_b = "CRP"
            elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                p_t_b = "CRD"

            if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                p_t_s = "CSH"
            elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                p_t_s = "CRP"
            elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                p_t_s = "CRD"

            deal_data = (ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                  SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                  ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy")))
                         .values('pk', 'Name_RUS', 'OperTypes', 'SendTransferType', 'ReceiveTransferType'))

            # for exchange_name in form.cleaned_data.get('ExchangePoints'):
            EPIDs = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                             flat=True)
            for EPID in EPIDs:
                Transfers = EP_ExchangeID.objects.filter(ExchangePointID=EPID).values_list('ExchangeTransferID',
                                                                                           flat=True)
                # for Transfer in list(form.cleaned_data.get('chosen_deals')):
                Transfer = str(deal_data[0]['pk'])
                # print(Transfers)
                # print(ExchangeName)
                # print(EPID)
                if Transfer not in Transfers:
                    # EP_Deals = {}
                    if pcc[0]['ContactType'] == 'PART':
                        param = 0
                    #     Deals = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list(
                    #         'ExchangeTransferID', flat=True)))
                    #     Deals.sort()
                    #
                    elif pcc[0]['ContactType'] == 'ORG':
                        param = 1
                    #     ExchangePoints = Users_PCCNTR.objects.get(TG_Contact=username, ContactType=
                    #     ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                    #         'ContactType_code']).ExchangePointID
                    #     EPIDs = []
                    #     if ';' in ExchangePoints:
                    #         while ";" in ExchangePoints:
                    #             ExchangePointID = ExchangePoints[:ExchangePoints.find(";")].strip()
                    #             EPIDs.append(ExchangePointID)
                    #             ExchangePoints = ExchangePoints[ExchangePoints.find(";") + 1:].strip()
                    #         EPIDs.append(ExchangePoints[1:].strip())
                    #     else:
                    #         EPIDs.append(ExchangePoints.strip())
                    #     EPIDs = list(set(EPIDs))
                    #     Deals = []
                    #     for EPID in EPIDs:
                    #         exch_deals = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                    #                                                            ExchangePointID=EPID).values_list(
                    #             'ExchangeTransferID', flat=True)))
                    #         for deal in exch_deals:
                    #             Deals.append(deal)
                    #
                    #     Deals = list(set(Deals))
                    #     Deals.sort()
                    #
                    # for deal in Deals:
                    #     exch_point_names = []
                    #     ExchangePointIDs = list(
                    #         set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                    #                                          ExchangeTransferID=deal).values_list(
                    #             'ExchangePointID', flat=True)))
                    #     ExchangePointIDs.sort()
                    #     for EPID in ExchangePointIDs:
                    #         EP_info = PCCNTR_ExchP.objects.get(PCCNTR=pcc_name.PCCNTR_code,
                    #                                            ExchangePointID=EPID)
                    #         exch_point_names.append(EP_info.ExchangePointName)
                    #     exch_point_names = list(set(exch_point_names))
                    #     exch_point_names.sort()
                    #     exch_point_names_str = ''
                    #     for EP in exch_point_names:
                    #         exch_point_names_str += str(EP) + ", "
                    #     exch_point_names_str = exch_point_names_str[:len(exch_point_names_str) - 2]
                    #     EP_Deals[deal] = exch_point_names_str

                    error = 'Выбрано направление сделки ' + str(
                        deal_data[0]['Name_RUS']) + ', которое на проводится в обменнике ' + str(ExchangeName) + '. '
                    return render(request, 'testsite/settings_general_change_exchange_deals_menu.html',
                                  context={'form': form, "param": param, 'EP_Deals': EP_Deals, 'error': error,
                                           'param2': 0, 'exch_name': ExchangeName})
                # else:
                #     EP_info = EP_ExchangeID.objects.get(ExchangePointID=EPID, ExchangeTransferID=Transfer)
                #     min.append(EP_info.ExchTOAmount_Min)
                #     max.append(EP_info.ExchTOAmount_Max)
                #     PRFTNORM = str(EP_info.EP_PRFTNORM)
                #     PRFTNORM = str(PRFTNORM[:PRFTNORM.find(' ')]) + " " + str(PRFTNORM[PRFTNORM.find(':'):])
                #     norm_prib.append(PRFTNORM)

        # for test_list in [min, max, norm_prib]:
        #     combinations = list(itertools.combinations(test_list, 2))
        #     for combination in combinations:
        #         if combination[0] != combination[1]:
        #             #print(combination)
        #             if pcc[0]['ContactType'] == 'PART':
        #                 param = 0
        #             elif pcc[0]['ContactType'] == 'ORG':
        #                 param = 1
        #             error = 'Разные данные по направлениям сделок'
        #             return render(request, 'testsite/settings_general_change_exchange_deals_menu.html',
        #                           context={'form': form, "param": param, 'EP_Deals': EP_Deals, 'error': error,
        #                                    'param2': 0, 'exch_name':ExchangeName})

            chosen_ep_deals = {}
            chosen_ep_deals['ExchangePoints'] = form.cleaned_data.get('ExchangePoints')
            chosen_ep_deals['Deals'] = str(deal_data[0]['pk'])
            cache.set('chosen_ep_deals', chosen_ep_deals)
            cache.delete('EP_Deals')
            return redirect('general_settings_change_exchange_deals_2')

    else:
        form = ChooseExchangePointsandDeals(request.user, usertype, ExchangeName)
        EP_Deals = {}
        if pcc[0]['ContactType'] == 'PART':
            param = 0
            Deals = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID',
                                                                                                   flat=True)))
            Deals.sort()

            for deal in Deals:
                exch_point_names = []
                ExchangePointIDs = list(
                    set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangeTransferID=deal).values_list(
                        'ExchangePointID', flat=True)))
                ExchangePointIDs.sort()

                for EPID in ExchangePointIDs:
                    EP_info = PCCNTR_ExchP.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID)
                    exch_point_names.append(EP_info.ExchangePointName)

                exch_point_names = list(set(exch_point_names))
                exch_point_names.sort()
                exch_point_names_str = ''

                for EP in exch_point_names:
                    exch_point_names_str += str(EP) + ", "
                exch_point_names_str = exch_point_names_str[:len(exch_point_names_str) - 2]
                EP_Deals[ExchangeID.objects.filter(pk=deal).values_list('Name_RUS',flat=True)[0]] = exch_point_names_str

        elif pcc[0]['ContactType'] == 'ORG':
            param = 1
            EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                           flat=True).order_by(
                'ExchangePointID')
            EPID_str = '; '.join(EPID)
            ExchangePoints = EPID_str
            EPIDs = []
            if ';' in ExchangePoints:
                while ";" in ExchangePoints:
                    ExchangePointID = ExchangePoints[:ExchangePoints.find(";")].strip()
                    EPIDs.append(ExchangePointID)
                    ExchangePoints = ExchangePoints[ExchangePoints.find(";") + 1:].strip()
                EPIDs.append(ExchangePoints[1:].strip())
            else:
                EPIDs.append(ExchangePoints.strip())
            EPIDs = list(set(EPIDs))
            Deals = []
            for EPID in EPIDs:
                exch_deals = list(
                    set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID).values_list(
                        'ExchangeTransferID', flat=True)))

                for deal in exch_deals:
                    Deals.append(deal)
            Deals = list(set(Deals))
            Deals.sort()

            for deal in Deals:
                EP_Deals[ExchangeID.objects.filter(pk=deal).values_list('Name_RUS',flat=True)[0]] = ExchangeName
        cache.set('EP_Deals', EP_Deals)
    return render(request, 'testsite/settings_general_change_exchange_deals_menu.html',
                  context={'form': form, 'title': 'Выбор обменника и направления сделок', "param": param,
                           'EP_Deals': EP_Deals, 'param2': 0, 'exch_name': ExchangeName})

#
def general_settings_change_exchange_deals_2(request):
    # global user_type, chosen_ep_deals
    # user_type = cache.get('user_type')
    chosen_ep_deals = cache.get('chosen_ep_deals')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=chosen_ep_deals['ExchangePoints']).values('ExchangePointID')[0]['ExchangePointID']
    ExchPDeal = EP_ExchangeID.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID, ExchangeTransferID=chosen_ep_deals['Deals'])
    exch_code = PCCNTR_ExchP.objects.filter(ExchangePointName=chosen_ep_deals['ExchangePoints']).values_list('pk', flat=True)[0]
    Norm_Prib = ExchPDeal.EP_PRFTNORM
    Norm_Prib_Name_1 = []
    Norm_Prib_Name_2 = []
    Norm_Prib_Percent = []
    if ';' in Norm_Prib:
        while ";" in Norm_Prib:
            N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
            Name = N_P[:N_P.find(' ')].strip()
            Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
            Name_1 = Name[:Name.find("-")].strip()
            Norm_Prib_Name_1.append(Name_1)
            Name_2 = Name[Name.find("-") + 1:].strip()
            Norm_Prib_Name_2.append(Name_2)
            Norm_Prib_Percent.append(Percent)
            Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()

        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
        Name_1 = Name[:Name.find("-")].strip()
        Norm_Prib_Name_1.append(Name_1)
        Name_2 = Name[Name.find("-") + 1:].strip()
        Norm_Prib_Name_2.append(Name_2)
        Norm_Prib_Percent.append(Percent)
    else:
        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
        Name_1 = Name[:Name.find("-")].strip()
        Norm_Prib_Name_1.append(Name_1)
        Name_2 = Name[Name.find("-") + 1:].strip()
        Norm_Prib_Name_2.append(Name_2)
        Norm_Prib_Percent.append(Percent)

    if len(Norm_Prib_Name_1) == 1:
        Norm_Prib_Name_1.append('')
        Norm_Prib_Name_2.append('')
        Norm_Prib_Name_1.append('')
        Norm_Prib_Name_2.append('')

    if len(Norm_Prib_Name_1) == 2:
        Norm_Prib_Name_1.append('')
        Norm_Prib_Name_2.append('')

    if len(Norm_Prib_Percent) == 1:
        Norm_Prib_Percent.append('')
        Norm_Prib_Percent.append('')

    if len(Norm_Prib_Percent) == 2:
        Norm_Prib_Percent.append('')

    if ExchPDeal.ExchTOAmount_Min is None:
        min_amount = ''
    else:
        min_amount = float(ExchPDeal.ExchTOAmount_Min)

    if ExchPDeal.ExchTOAmount_Max is None:
        max_amount = ''
    else:
        max_amount = float(ExchPDeal.ExchTOAmount_Max)

    if request.method == 'POST':
        form = ChangeDealInfo(request.POST)
        if form.is_valid():


            # for EP in chosen_ep_deals['ExchangePoints']:
            #     for deal in chosen_ep_deals['Deals']:
            EPIDs = PCCNTR_ExchP.objects.filter(ExchangePointName=chosen_ep_deals['ExchangePoints']).values_list('ExchangePointID', flat=True)
            for EPID in EPIDs:
                EP_deal = EP_ExchangeID.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID,
                                                    ExchangeTransferID=chosen_ep_deals['Deals'])

                if str(form.cleaned_data.get('Min_amount')) != EP_deal.ExchTOAmount_Min:
                    EP_deal.ExchTOAmount_Min = form.cleaned_data.get('Min_amount')

                if str(form.cleaned_data.get('Max_amount')) != EP_deal.ExchTOAmount_Max:
                    EP_deal.ExchTOAmount_Max = form.cleaned_data.get('Max_amount')


                deal_name = ExchangeID.objects.filter(pk=chosen_ep_deals['Deals']).values_list('Name_RUS',flat=True)[0]
                curr_to = deal_name[deal_name.find(">") + 2:]
                curr_to = curr_to[:curr_to.find(" ")]

                if form.cleaned_data.get('Norm_Prib_Name_1_1') == form.cleaned_data.get('Min_amount'):
                    Norm_Prib = str(form.cleaned_data.get('Norm_Prib_Name_1_1')) + "-" + str(
                        form.cleaned_data.get('Norm_Prib_Name_1_2')) + " " + curr_to + ": " + str(
                        form.cleaned_data.get('Norm_Prib_Percent_1')) + "%" + "; "

                    if str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_2_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) + "%" + "; "

                    elif form.cleaned_data.get('Norm_Prib_Name_1_2') != form.cleaned_data.get('Max_amount'):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 1
                                          , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                          , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "") and (
                            form.cleaned_data.get('Norm_Prib_Name_1_2') + 1 != form.cleaned_data.get('Norm_Prib_Name_2_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 1
                                          , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                          , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                    if str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "":
                        Norm_Prib = Norm_Prib + str(form.cleaned_data.get('Norm_Prib_Name_3_1')) + "-" + str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) + " " + curr_to + ": " + str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) + "%" + "; "

                    elif (str(form.cleaned_data.get('Norm_Prib_Name_2_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_2_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_2')) != "") and (
                            str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                        form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and (
                            form.cleaned_data.get('Norm_Prib_Name_2_2') != form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 1
                                          , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                          , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                        form.cleaned_data.get('Norm_Prib_Name_2_2')) + 1 != float(
                        form.cleaned_data.get('Norm_Prib_Name_3_1')):
                        error = 'Присутствуют пропуски в промежутках нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 1
                                          , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                          , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                    if (str(form.cleaned_data.get('Norm_Prib_Name_3_1')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Name_3_2')) != "" and str(
                            form.cleaned_data.get('Norm_Prib_Percent_3')) != "") and float(
                        form.cleaned_data.get('Norm_Prib_Name_3_2')) != float(
                        form.cleaned_data.get('Max_amount')):
                        error = 'Максимальная сумма сделки не совпадает с окончанием промужутка нормы прибыльности'
                        return render(request, 'testsite/settings_general_exchange_deals.html',
                                      {'form': form, 'title': 'Направления сделок', 'param': 1
                                          , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                          , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                else:
                    error = 'Минимальная сумма сделки не совпадает с началом промужутка нормы прибыльности'
                    return render(request, 'testsite/settings_general_exchange_deals.html',
                                  {'form': form, 'title': 'Направления сделок', 'param': 1
                                      , 'EP': ', '.join(chosen_ep_deals['ExchangePoints'])
                                      , 'Deals': ', '.join(chosen_ep_deals['Deals']), 'error': error})

                Norm_Prib = Norm_Prib[:len(Norm_Prib) - 2]
                if Norm_Prib != EP_deal.EP_PRFTNORM:
                    EP_deal.EP_PRFTNORM = Norm_Prib

                EP_deal.save()
                cache.delete('chosen_ep_deals')
            return redirect('general_settings_exchange_points')

    else:
        form = ChangeDealInfo(initial={'Min_amount': min_amount,
                                       'Max_amount': max_amount,
                                       'Norm_Prib_Name_1_1': Norm_Prib_Name_1[0],
                                       'Norm_Prib_Name_1_2': Norm_Prib_Name_2[0],
                                       'Norm_Prib_Percent_1': Norm_Prib_Percent[0],
                                       'Norm_Prib_Name_2_1': Norm_Prib_Name_1[1],
                                       'Norm_Prib_Name_2_2': Norm_Prib_Name_2[1],
                                       'Norm_Prib_Percent_2': Norm_Prib_Percent[1],
                                       'Norm_Prib_Name_3_1': Norm_Prib_Name_1[2],
                                       'Norm_Prib_Name_3_2': Norm_Prib_Name_2[2],
                                       'Norm_Prib_Percent_3': Norm_Prib_Percent[2],
                                       })
        deal_name = ExchangeID.objects.filter(pk=chosen_ep_deals['Deals']).values_list('Name_RUS',flat=True)[0]
    return render(request, 'testsite/settings_general_exchange_deals.html',
                  {'form': form, 'title': 'Направления сделок', 'param': 1, 'EP': chosen_ep_deals['ExchangePoints'],
                                'Deals': deal_name, 'exch_code': exch_code})

#
def general_settings_delete_exchange_deals(request):
    # global user_type, chosen_ep_deals, EP_Deals, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    EP_Deals = cache.get('EP_Deals')
    username = request.user
    usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
        'ContactType_code']
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "PART":
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user).values('TG_Contact', 'ContactType', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "ORG":
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        EPID_str = '; '.join(EPID)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ContactType='ORG', ExchangePointID=EPID_str).values(
            'TG_Contact', 'ContactType',
            'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])

    if request.method == 'POST':
        form = ChooseExchangePointsandDeals(request.user, usertype, ExchangeName, request.POST)
        if form.is_valid():
            p_t_b = ""
            p_t_s = ""
            if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                p_t_b = "CSH"
            elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                p_t_b = "CRP"
            elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                p_t_b = "CRD"

            if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                p_t_s = "CSH"
            elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                p_t_s = "CRP"
            elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                p_t_s = "CRD"

            deal_data = (ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                  SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                  ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy")))
                         .values('pk', 'Name_RUS', 'OperTypes', 'SendTransferType', 'ReceiveTransferType'))
            # for exchange_name in form.cleaned_data.get('ExchangePoints'):
            EPIDs = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                ExchangePointName=form.cleaned_data.get('ExchangePoints')).values_list('ExchangePointID',flat=True)
            for EPID in EPIDs:
                Transfers = EP_ExchangeID.objects.filter(ExchangePointID=EPID).values_list('ExchangeTransferID',
                                                                                           flat=True)
                # for Transfer in list(form.cleaned_data.get('chosen_deals')):
                Transfer = str(deal_data[0]['pk'])
                if Transfer not in Transfers:
                    # EP_Deals = {}
                    if pcc[0]['ContactType'] == 'PART':
                        param = 0
                    elif pcc[0]['ContactType'] == 'ORG':
                        param = 1
                    error = 'Выбрано направление сделки ' + str(
                        Transfer) + ', которое на проводится в обменнике ' + str(ExchangeName) + '. '
                    return render(request, 'testsite/settings_general_change_exchange_deals_menu.html',
                                  context={'form': form, "param": param, 'EP_Deals': EP_Deals, 'param2': 1, 'exch_name': ExchangeName, 'error': error})

            chosen_ep_deals = {}
            chosen_ep_deals['ExchangePoints'] = form.cleaned_data.get('ExchangePoints')
            chosen_ep_deals['Deals'] = str(deal_data[0]['pk'])
            cache.set('chosen_ep_deals', chosen_ep_deals)
            cache.delete('EP_Deals')
            return redirect('general_settings_delete_exchange_deals_confirm')
    else:
        form = ChooseExchangePointsandDeals(request.user, usertype, ExchangeName)
        EP_Deals = {}
        if pcc[0]['ContactType'] == 'PART':
            param = 0
            Deals = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID',
                                                                                                   flat=True)))
            Deals.sort()
            for deal in Deals:
                exch_point_names = []
                ExchangePointIDs = list(
                    set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangeTransferID=deal).values_list(
                        'ExchangePointID', flat=True)))
                ExchangePointIDs.sort()
                for EPID in ExchangePointIDs:
                    EP_info = PCCNTR_ExchP.objects.get(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID)
                    exch_point_names.append(EP_info.ExchangePointName)
                exch_point_names = list(set(exch_point_names))
                exch_point_names.sort()
                exch_point_names_str = ''
                for EP in exch_point_names:
                    exch_point_names_str += str(EP) + ", "
                exch_point_names_str = exch_point_names_str[:len(exch_point_names_str) - 2]
                EP_Deals[ExchangeID.objects.filter(pk=deal).values_list('Name_RUS', flat=True)[0]] = exch_point_names_str

        elif pcc[0]['ContactType'] == 'ORG':
            param = 1
            EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                flat=True).order_by('ExchangePointID')
            EPID_str = '; '.join(EPID)
            ExchangePoints = EPID_str
            EPIDs = []
            if ';' in ExchangePoints:
                while ";" in ExchangePoints:
                    ExchangePointID = ExchangePoints[:ExchangePoints.find(";")].strip()
                    EPIDs.append(ExchangePointID)
                    ExchangePoints = ExchangePoints[ExchangePoints.find(";") + 1:].strip()
                EPIDs.append(ExchangePoints[1:].strip())
            else:
                EPIDs.append(ExchangePoints.strip())
            EPIDs = list(set(EPIDs))
            Deals = []
            for EPID in EPIDs:
                exch_deals = list(
                    set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID).values_list(
                        'ExchangeTransferID', flat=True)))
                for deal in exch_deals:
                    Deals.append(deal)

            Deals = list(set(Deals))
            Deals.sort()
            for deal in Deals:
                EP_Deals[ExchangeID.objects.filter(pk=deal).values_list('Name_RUS', flat=True)[0]] = ExchangeName

        cache.set('EP_Deals', EP_Deals)
    return render(request, 'testsite/settings_general_change_exchange_deals_menu.html', context={'form': form
        , 'title': 'Выбор обменника и направления сделок', "param": param, 'EP_Deals': EP_Deals, 'param2': 1, 'exch_name': ExchangeName})

#
def general_settings_delete_exchange_deals_confirm(request):
    # global user_type, chosen_ep_deals
    # user_type = cache.get('user_type')
    chosen_ep_deals = cache.get('chosen_ep_deals')
    return render(request, 'testsite/settings_general_delete_exchange_deals_confirm.html',
                  {'title': 'Подтверждение удаления направлений сделок', 'EP': chosen_ep_deals['ExchangePoints']
                      , 'Deals': ExchangeID.objects.filter(pk=chosen_ep_deals['Deals'])
                                                                    .values_list('Name_RUS', flat=True)[0], 'param': 0})

#
def general_settings_delete_exchange_deals_final(request):
    # global user_type, chosen_ep_deals
    # user_type = cache.get('user_type')
    chosen_ep_deals = cache.get('chosen_ep_deals')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    # pcc_opertypes = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list("OperType",
    #                                                                                          flat=True)
    # pcc_opertypes = list(set(list(pcc_opertypes)))

    # for EP in chosen_ep_deals['ExchangePoints']:
    #     for deal in chosen_ep_deals['Deals']:

    EPIDs = PCCNTR_ExchP.objects.filter(ExchangePointName=chosen_ep_deals['ExchangePoints']).values_list('ExchangePointID', flat=True)
    for EPID in EPIDs:
        EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID=EPID,
                                     ExchangeTransferID=chosen_ep_deals['Deals']).delete()
    # Exchange_Transfers = list(
    #     set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID', flat=True)))
    # for opertype in pcc_opertypes:
    #     if opertype not in Exchange_Transfers:
    #         PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, OperType=opertype).delete()

    ExchangeTranfersID = list(set(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID', flat=True)))
    opertypes_list = list(set(ExchangeID.objects.filter(pk__in=ExchangeTranfersID).values_list('OperTypes', flat=True)))

    OPRTs = []
    for opertype in opertypes_list:
        if ';' in opertype:
            while ';' in opertype:
                oprt = opertype[:opertype.find(";")].strip()
                OPRTs.append(oprt)
                opertype = opertype[opertype.find(";") + 1:].strip()
            OPRTs.append(opertype.strip())
        else:
            OPRTs.append(opertype.strip())

    OPRTs = list(set(OPRTs))

    PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).exclude(OperType__in=OPRTs).delete()
    cache.delete('chosen_ep_deals')
    return redirect('general_settings_exchange_points')

#
def general_settings_change_exchange_deals_bonus_2(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type=='Партнер':
        PCCNTR_code = Users_PCCNTR.objects.get(TG_Contact=request.user, ContactType=ContactType.objects.get(Name_RUS=user_type).ContactType_code)
    else:
        PCCNTR_code = Users_PCCNTR.objects.get(TG_Contact=request.user, ExchangePointID__contains=
                                                                                PCCNTR_ExchP.objects.filter(
                                                                                    ExchangePointName=ExchangeName).
                                                                                        values_list('ExchangePointID', flat=True)[0],
                                               ContactType=ContactType.objects.get(Name_RUS=user_type).ContactType_code)
    BonusProgramm = PCCNTR.objects.get(PCCNTR_code=PCCNTR_code.PCCNTR)

    Norm_Prib = BonusProgramm.Bonus
    if Norm_Prib != '-':
        Norm_Prib_Name_1 = []
        Norm_Prib_Name_2 = []
        Norm_Prib_Percent = []
        Currency = Norm_Prib[Norm_Prib.find(' ')+1:Norm_Prib.find(':')]
        if ';' in Norm_Prib:
            while ";" in Norm_Prib:
                N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
                Name = N_P[:N_P.find(' ')].strip()
                Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
                Name_1 = Name[:Name.find("-")].strip()
                Norm_Prib_Name_1.append(Name_1)
                Name_2 = Name[Name.find("-") + 1:].strip()
                Norm_Prib_Name_2.append(Name_2)
                Norm_Prib_Percent.append(Percent)
                Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
            Name = Norm_Prib[:Norm_Prib.find(' ')].strip()

            Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
            Name_1 = Name[:Name.find("-")].strip()
            Norm_Prib_Name_1.append(Name_1)
            Name_2 = Name[Name.find("-") + 1:].strip()
            Norm_Prib_Name_2.append(Name_2)
            Norm_Prib_Percent.append(Percent)
        else:
            Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
            Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
            Name_1 = Name[:Name.find("-")].strip()
            Norm_Prib_Name_1.append(Name_1)
            Name_2 = Name[Name.find("-") + 1:].strip()
            Norm_Prib_Name_2.append(Name_2)
            Norm_Prib_Percent.append(Percent)

        if len(Norm_Prib_Name_1) == 1:
            Norm_Prib_Name_1.append('')
            Norm_Prib_Name_2.append('')
            Norm_Prib_Name_1.append('')
            Norm_Prib_Name_2.append('')

        if len(Norm_Prib_Name_1) == 2:
            Norm_Prib_Name_1.append('')
            Norm_Prib_Name_2.append('')

        if len(Norm_Prib_Percent) == 1:
            Norm_Prib_Percent.append('')
            Norm_Prib_Percent.append('')

        if len(Norm_Prib_Percent) == 2:
            Norm_Prib_Percent.append('')

        # print(Norm_Prib_Name_1)
        # print(Norm_Prib_Name_2)
        # print(Norm_Prib_Percent)
        # print(Currency)

    if request.method == 'POST':
        form = ChooseDealsInfo_bonus(request.POST)
        if form.is_valid():

            if float(form.cleaned_data.get('Bonus_Name_1_2')) + 1 != float(
                    form.cleaned_data.get('Bonus_Name_2_1')) or (
                    float(form.cleaned_data.get('Bonus_Name_2_2')) + 1 != float(
                    form.cleaned_data.get('Bonus_Name_3_1'))):
                error = 'Присутствуют пропуски в промежутках скидочной программы'
                return render(request, 'testsite/settings_general_exchange_deals.html',
                          {'form': form, 'title': 'Направления сделок', 'param': 4,
                           'EP': '-',
                           'Deals': '-', 'exch_code': '-', 'error':error})

            New_Bonus = (str(form.cleaned_data.get('Bonus_Name_1_1')) + "-" + str(
                form.cleaned_data.get('Bonus_Name_1_2'))
                     + " " + str(form.cleaned_data.get('Usdt_or_eur')) + ": " + str(
                        form.cleaned_data.get('Bonus_Percent_1'))
                     + "%" + "; " + str(form.cleaned_data.get('Bonus_Name_2_1')) + "-" + str(
                        form.cleaned_data.get('Bonus_Name_2_2')) + " " + str(
                        form.cleaned_data.get('Usdt_or_eur')) + ": "
                     + str(form.cleaned_data.get('Bonus_Percent_2')) + "%" + "; " + str(
                        form.cleaned_data.get('Bonus_Name_3_1'))
                     + "+ " + str(form.cleaned_data.get('Usdt_or_eur')) + ": " + str(
                        form.cleaned_data.get('Bonus_Percent_3')) + "%")

            if New_Bonus != BonusProgramm.Bonus:
                BonusProgramm.Bonus = New_Bonus

            BonusProgramm.save()

            return redirect('balance_settings')

    else:
        if Norm_Prib != '-':
            form = ChooseDealsInfo_bonus(initial={'Usdt_or_eur': Currency,
                                                   'Bonus_Name_1_1': 0,
                                                   'Bonus_Name_1_2': Norm_Prib_Name_2[0],
                                                   'Bonus_Percent_1': Norm_Prib_Percent[0],
                                                   'Bonus_Name_2_1': Norm_Prib_Name_1[1],
                                                   'Bonus_Name_2_2': Norm_Prib_Name_2[1],
                                                   'Bonus_Percent_2': Norm_Prib_Percent[1],
                                                   'Bonus_Name_3_1': Norm_Prib_Name_1[2],
                                                   'Bonus_Name_3_2': "+",
                                                   'Bonus_Percent_3': Norm_Prib_Percent[2],
                                                   })
        else:
            form = ChooseDealsInfo_bonus(initial={'Bonus_Name_1_1': 0,
                                                  'Bonus_Name_3_2': "+",
                                                  })
    return render(request, 'testsite/settings_general_exchange_deals.html',
                  {'form': form, 'title': 'Направления сделок', 'param': 4, 'EP': '-',
                                'Deals': '-', 'exch_code': '-'})

#
def general_settings_change_exchange_rate_source(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "PART":
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        Quotes = QuotesRC.objects.all().values_list('QuotesRC_Code', flat=True)
        All_OperTypes = list(PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, QuotesRC__in=Quotes).values_list("OperType", 'QuotesRC').order_by("OperType"))
        # Currency_types = ExchangeID.objects.filter(
        #     Name_RUS__in=PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, QuotesRC__in=Quotes).values_list("OperType",
        #                                                                              flat=True)).values_list(
        #     "SendTransferType", "ReceiveTransferType").order_by("Name_RUS")
    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == "ORG":
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        EP_TransferID = EP_ExchangeID.objects.filter(ExchangePointID__in=EPID).values_list('ExchangeTransferID',
                                                                                          flat=True).distinct()
        EP_OperTypes = ExchangeID.objects.filter(pk__in=EP_TransferID).values_list('OperTypes',
                                                                                          flat=True).distinct()
        OPRTs = []
        for opertype in EP_OperTypes:
            if ';' in opertype:
                while ';' in opertype:
                    oprt = opertype[:opertype.find(";")].strip()
                    OPRTs.append(oprt)
                    opertype = opertype[opertype.find(";") + 1:].strip()
                OPRTs.append(opertype.strip())
            else:
                OPRTs.append(opertype.strip())

        EPID_str = '; '.join(EPID)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ContactType='ORG', ExchangePointID=EPID_str).values(
            'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        Quotes = QuotesRC.objects.all().values_list('QuotesRC_Code', flat=True)
        All_OperTypes = list(PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, QuotesRC__in=Quotes,
                                                        OperType__in=OPRTs).values_list(
            "OperType", 'QuotesRC').order_by("OperType"))
        # Currency_types = ExchangeID.objects.filter(
        #     Name_RUS__in=PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, QuotesRC__in=Quotes,
        #                                                  OperType__in=EP_OperTypes).values_list(
        #         "OperType", flat=True)).values_list("SendTransferType", "ReceiveTransferType").order_by("Name_RUS")
    # print(All_OperTypes)
    num = len(All_OperTypes)
    Opertypes = {}
    # print(num)
    for i in range(len(All_OperTypes)):
        Opertypes['N_' + str(i)] = All_OperTypes[i][0]

    if request.method == 'POST':
        form = ChooseSourceforExchDeals(All_OperTypes, request.POST)
        if form.is_valid():
            if num == 1:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1']]
            elif num == 2:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2']]
            elif num == 3:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3']]
            elif num == 4:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3'], ['chosen_quote_4', 'chosen_bank_4']]
            elif num == 5:
                Used_form_fields = [['chosen_quote_1', 'chosen_bank_1'], ['chosen_quote_2', 'chosen_bank_2'],
                                    ['chosen_quote_3', 'chosen_bank_3'], ['chosen_quote_4', 'chosen_bank_4'],
                                    ['chosen_quote_5', 'chosen_bank_5']]

            for i in range(len(Used_form_fields)):
                Opertype = PCCNTR_OperTypes.objects.get(PCCNTR=pcc_name.PCCNTR_code, OperType=All_OperTypes[i][0])
                #print(form.cleaned_data.get(Used_form_fields[i][0]))
                if Opertype.QuotesRC != \
                        QuotesRC.objects.filter(Name_RUS=form.cleaned_data.get(Used_form_fields[i][0])).values(
                                'QuotesRC_Code')[0]['QuotesRC_Code']:
                    Opertype.QuotesRC = \
                    QuotesRC.objects.filter(Name_RUS=form.cleaned_data.get(Used_form_fields[i][0])).values(
                        'QuotesRC_Code')[0]['QuotesRC_Code']
                    Opertype.save()

                # if Opertype.Bank != form.cleaned_data.get(Used_form_fields[i][1]):
                #     Opertype.Bank = form.cleaned_data.get(Used_form_fields[i][1])
                #     Opertype.save()

            return redirect('general_settings_exchange_points')
    else:
        if num == 1:
            form = ChooseSourceforExchDeals(All_OperTypes, initial={
                'chosen_quote_1': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[0][1]).values('Name_RUS')[0][
                    'Name_RUS']})
        elif num == 2:
            form = ChooseSourceforExchDeals(All_OperTypes, initial={
                'chosen_quote_1': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[0][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_2': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[1][1]).values('Name_RUS')[0][
                    'Name_RUS']})
        elif num == 3:
            form = ChooseSourceforExchDeals(All_OperTypes, initial={
                'chosen_quote_1': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[0][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_2': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[1][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_3': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[2][1]).values('Name_RUS')[0][
                    'Name_RUS']})
        elif num == 4:
            form = ChooseSourceforExchDeals(All_OperTypes, initial={
                'chosen_quote_1': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[0][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_2': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[1][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_3': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[2][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_4': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[3][1]).values('Name_RUS')[0][
                    'Name_RUS']})
        elif num == 5:
            form = ChooseSourceforExchDeals(All_OperTypes, initial={
                'chosen_quote_1': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[0][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_2': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[1][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_3': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[2][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_4': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[3][1]).values('Name_RUS')[0][
                    'Name_RUS'],
                'chosen_quote_5': QuotesRC.objects.filter(QuotesRC_Code=All_OperTypes[4][1]).values('Name_RUS')[0][
                    'Name_RUS']})

    return render(request, 'testsite/settings_general_exchange_rate_source.html',
                  {'form': form, 'title': 'Источники курсов валют', 'Opertypes': Opertypes, 'num': num, 'param': 1})

#
def general_settings_personal(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    if user_type != 'Партнер' and user_type != 'Клиент':
        ExchangeName = urllib.parse.unquote(ExchangeName)
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    username = request.user
    user = Users.objects.filter(TG_Contact=username).values('Surname', 'Name', 'Otchestvo', 'GENDER', 'COUNTRY', 'CITY',
                                                            'Language')

    if request.method == 'POST':
        form = ChangePersonalInformation(request.POST)
        if form.is_valid():
            username = request.user
            user = Users.objects.get(TG_Contact=username)

            if str(form.cleaned_data.get('Surname')) != "":
                user.Surname = form.cleaned_data['Surname']
            if str(form.cleaned_data.get('Name')) != "":
                user.Name = form.cleaned_data['Name']
            if str(form.cleaned_data['Otchestvo']) != "":
                user.Otchestvo = form.cleaned_data['Otchestvo']
            if form.cleaned_data.get('GENDER') is not None:
                gender = Gender.objects.filter(Name_RUS=form.cleaned_data['GENDER']).values('Gender_code')
                user.GENDER = gender[0]['Gender_code']
            if form.cleaned_data.get('COUNTRY') is not None and form.cleaned_data.get('CITY') is not None:
                city = Cities.objects.filter(Name_RUS=form.cleaned_data['CITY']).values('City_code', 'Country')
                country = Countries.objects.filter(Name_RUS=form.cleaned_data['COUNTRY']).values('Country_code')
                if str(country[0]['Country_code']) == str(city[0]['Country']):
                    user.COUNTRY = country[0]['Country_code']
                    user.CITY = city[0]['City_code']
                else:
                    form = ChangePersonalInformation(request.POST)
                    error = 'Выбранный Вами город находится в другой стране, поэтому необходимо изменить страну'
                    return render(request, 'testsite/settings_general_personal.html',
                                  {'form': form, 'title': 'Изменение персональных данных', 'error': error, 'usertype':
                                      ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                                          'ContactType_code']})
                # country = Countries.objects.filter(Name_RUS=form.cleaned_data['COUNTRY']).values('Country_code')
                # user.COUNTRY = country[0]['Country_code']
                # city = Cities.objects.filter(Name_RUS=form.cleaned_data['CITY']).values('City_code')
                # user.CITY = city[0]['City_code']
            # elif form.cleaned_data.get('COUNTRY') is not None:
            #     form = ChangePersonalInformation(request.POST)
            #     error = 'При изменении страны необходимо изменить город'
            #     return render(request, 'testsite/settings_general_personal.html',
            #                   {'form': form, 'title': 'Изменение персональных данных', 'error': error})
            # elif form.cleaned_data.get('CITY') is not None:
            #     city = Cities.objects.filter(Name_RUS=form.cleaned_data['CITY']).values('City_code', 'Country')
            #     if str(user.COUNTRY) == str(city[0]['Country']):
            #         user.CITY = city[0]['City_code']
            #     else:
            #         form = ChangePersonalInformation(request.POST)
            #         error = 'Выбранный Вами город находится в другой стране, поэтому необходимо изменить страну'
            #         return render(request, 'testsite/settings_general_personal.html',
            #                       {'form': form, 'title': 'Изменение персональных данных', 'error': error})
            if form.cleaned_data.get('Language') != 'Язык не выбран':
                user.Language = str(form.cleaned_data.get('Language'))
            user.save()
            return redirect('home', usertype)
        else:
            city = Cities.objects.filter(City_code=user[0]['CITY']).values('Name_RUS')[0]['Name_RUS']
            gender = Gender.objects.filter(Gender_code=user[0]['GENDER']).values('Name_RUS')[0]['Name_RUS']
            country = Countries.objects.filter(Country_code=user[0]['COUNTRY']).values('Name_RUS')[0]['Name_RUS']

            form = ChangePersonalInformation(
                initial={'Surname': user[0]['Surname'], 'Name': user[0]['Name'], 'Otchestvo': user[0]['Otchestvo'],
                         'CITY': city, 'COUNTRY': country, 'GENDER': gender})
            error = ''
    else:
        city = Cities.objects.filter(City_code=user[0]['CITY']).values('Name_RUS')[0]['Name_RUS']
        gender = Gender.objects.filter(Gender_code=user[0]['GENDER']).values('Name_RUS')[0]['Name_RUS']
        country = Countries.objects.filter(Country_code=user[0]['COUNTRY']).values('Name_RUS')[0]['Name_RUS']
        form = ChangePersonalInformation(
            initial={'Surname': user[0]['Surname'], 'Name': user[0]['Name'], 'Otchestvo': user[0]['Otchestvo'],
                     'CITY': city, 'COUNTRY': country, 'GENDER': gender})
        error = ''
    if user_type != 'Партнер' and user_type != 'Клиент':
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    return render(request, 'testsite/settings_general_personal.html',
                  {'form': form, 'title': 'Изменение персональных данных', 'error': error,
                   'usertype': usertype})

#
def balance_settings(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user
    if user_type != 'Партнер' and user_type != 'Организатор' and user_type != 'Клиент':
        User_info = ''
        usertype = ExchangeName
        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID', flat=True)
        user_pccntr = Users_PCCNTR.objects.get(TG_Contact=username, ContactType__in=job_positions,
                                               ExchangePointID__in=EPID)
        if '; ' in user_pccntr.ContactType:
            contacttype = 'Куратор'
        else:
            contacttype = ContactType.objects.filter(ContactType_code=user_pccntr.ContactType).values('Name_RUS')[0][
                'Name_RUS']
        pcc_name = PCCNTR.objects.get(PCCNTR_code=user_pccntr.PCCNTR).PCCNTR_name
        PCCNTR_name = PCCNTR.objects.filter(PCCNTR_code=user_pccntr.PCCNTR).values("PCCNTR_name", 'Balance', "Reserve").distinct()
        for pccntr in PCCNTR_name:
            pccntr['Available'] = pccntr['Balance'] - pccntr['Reserve']

    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR', 'ContactType',
                                                                      'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
        contacttype = pcc[0]['ContactType']
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат
        # ExchangePoints = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values("ExchangePointName",
        #                                                                                  'Balance',
        #                                                                                  "bonusPercentFull").order_by(
        #     'ExchangePointName').distinct()
        PCCNTR_name = PCCNTR.objects.filter(PCCNTR_code=pcc_name.PCCNTR_code).values("PCCNTR_name", 'Balance', "Reserve").distinct()
        for pccntr in PCCNTR_name:
            pccntr['Available'] = pccntr['Balance'] - pccntr['Reserve']
        ExchangeName = ''
        User_info = ''

    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'ORG':
        User_info = ''
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        EPID_str = '; '.join(EPID)
        user_pccntr = Users_PCCNTR.objects.get(TG_Contact=username, ContactType='ORG', ExchangePointID=EPID_str)
        contacttype = user_pccntr.ContactType
        PCCNTR_name = PCCNTR.objects.filter(PCCNTR_code=user_pccntr.PCCNTR).values("PCCNTR_name", 'Balance',
                                                                                     "Reserve").distinct()
        for pccntr in PCCNTR_name:
            pccntr['Available'] = pccntr['Balance'] - pccntr['Reserve']

    elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'CLI':
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
        ExchangeName = ''
        PCCNTR_name = ''
        User_info = Users.objects.filter(TG_Contact=username).values("TG_Contact", 'ContactType', 'balanceFull',
                                                                     "bonusPercentFull").order_by("TG_Contact")
        contacttype = User_info[0]['ContactType']


    if len(PCCNTR_name) == 1:
        param = 0
    else:
        param = 1
    param2 = 0
    for ExchP in PCCNTR_name:
        if ExchP['Balance'] != 0:
            param2 += 1

    if User_info != "":
        if User_info[0]['balanceFull'] != 0:
            param2 += 1

    context = {
        "title": "Баланс и бонусы",
        "ContactType": contacttype,
        "PCCNTRs": PCCNTR_name,
        "param": param,
        "param2": param2,
        'usertype': usertype,
        'ExchangeName': ExchangeName,
        'User_info': User_info
    }
    return render(request, 'testsite/settings_balance.html', context=context)

#
def balance_settings_refill_balance(request):
    # global user_type
    user_type = cache.get('user_type')
    username = request.user
    usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR']).PCCNTR_name
    else:
        pcc_name= ''
    if request.method == 'POST':
        form = RefillBalance(request.POST)
        if form.is_valid():
            Payments_data = Payments.objects.all().values_list("Payment_data", flat=True)
            if form.cleaned_data.get("Payment_code") not in list(Payments_data):
                if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':

                    pccntr = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
                    pccntr.Balance += int(form.cleaned_data.get("balance_Amount"))
                    pccntr.save()
                    Payments.objects.create(TG_Contact=username, PCCNTR=pcc[0]['PCCNTR'],
                                           Blockchain='TRC20',
                                           Balance_Amount=form.cleaned_data.get("balance_Amount"),
                                           Payment_data=form.cleaned_data.get("Payment_code"),
                                           Payment_type='Пополнение баланса обменника')
                elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                    'ContactType_code'] == 'CLI':
                    user_info = Users.objects.get(TG_Contact=username)
                    user_info.balanceFull += int(form.cleaned_data.get("balance_Amount"))
                    user_info.save()
                    Payments.objects.create(TG_Contact=username, Blockchain='TRC20',
                                           Balance_Amount=form.cleaned_data.get("balance_Amount"),
                                           Payment_data=form.cleaned_data.get("Payment_code"),
                                           Payment_type='Пополнение баланса клиента')
                return redirect('balance_settings')
            else:
                error = "По данному хэшу транзакции уже совершено полопнение"
                return render(request, 'testsite/settings_balance_refill_balance.html',
                              {'form': form, 'title': 'Пополнение баланса', "error": error, 'usertype': usertype})

    else:
        form = RefillBalance()
    return render(request, 'testsite/settings_balance_refill_balance.html',
                  {'form': form, 'title': 'Пополнение баланса', 'usertype': usertype, 'pcc_name': pcc_name})

#
def balance_settings_withdraw_funds(request):
    user_type = cache.get('user_type')
    username = request.user
    usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code']
    if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR']).PCCNTR_name
    else:
        pcc_name = ''
    if request.method == 'POST':
        form = WithdrawBalance(request.POST)
        if form.is_valid():
            if ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0]['ContactType_code'] == 'PART':
                pccntr = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
                if pccntr.Balance - pccntr.Reserve >= int(form.cleaned_data.get("balance_Amount")):
                    pccntr.Balance -= int(form.cleaned_data.get("balance_Amount"))
                else:
                    error = "Запрашиваемая сумма для вывода превышает доступные средства обменника - " + str(
                        pccntr.Balance - pccntr.Reserve) + " USDT"
                    return render(request, 'testsite/settings_balance_withdraw_funds.html',
                                  {'form': form, 'title': 'Вывод средств', 'error': error, 'usertype': usertype})
                pccntr.save()
                Payments.objects.create(TG_Contact=username, PCCNTR=pcc[0]['PCCNTR'],
                                       Blockchain=form.cleaned_data.get("Blockchain_transfer"),
                                       Balance_Amount=int(form.cleaned_data.get("balance_Amount")) * -1,
                                       Payment_data=" - ",
                                       Payment_type='Вывод средств обменника')

            elif ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                'ContactType_code'] == 'CLI':
                user_info = Users.objects.get(TG_Contact=username)
                if user_info.balanceFull >= int(form.cleaned_data.get("balance_Amount")):
                    user_info.balanceFull -= int(form.cleaned_data.get("balance_Amount"))
                else:
                    error = "Запрашиваемая сумма для вывода превышает баланс клиента - " + str(
                        user_info.balanceFull) + " USDT"
                    return render(request, 'testsite/settings_balance_withdraw_funds.html',
                                  {'form': form, 'title': 'Вывод средств', 'error': error, 'usertype': usertype})

                user_info.save()
                Payments.objects.create(TG_Contact=username,
                                       Blockchain=form.cleaned_data.get("Blockchain_transfer"),
                                       Balance_Amount=int(form.cleaned_data.get("balance_Amount")) * -1,
                                       Payment_data=" - ",
                                       Payment_type='Вывод средств клиента')
            return redirect('balance_settings')
    else:
        form = WithdrawBalance()
    return render(request, 'testsite/settings_balance_withdraw_funds.html',
                  {'form': form, 'title': 'Вывод средств', 'usertype': usertype, 'pcc_name': pcc_name})

#
def P2Pmarket(request):
    # global user_type, ExchangeName
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    cache.delete('orders_for_board')
    if user_type != 'Партнер' and user_type != 'Клиент':
        ExchangeName = urllib.parse.unquote(ExchangeName)
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    context = {
        'usertype': usertype,
    }

    return render(request, 'testsite/P2Pmarket.html', context=context)

def load_pay_type_sell(request):
    currency_to_sell = request.GET.get('Currency_to_sell')
    currency_types = list(set(ExchangeID.objects.filter(SendCurrencyISO=currency_to_sell).values_list("SendTransferType",flat=True)))
    currency_types_for_form = []
    if 'CRP' in currency_types:
        currency_types_for_form.append('Перевод по сети блокчейн')
    if 'CSH' in currency_types:
        currency_types_for_form.append('Наличные')
    if 'CRD' in currency_types:
        currency_types_for_form.append('Карточный перевод')
    currency_types_for_form.sort()
    return render(request, 'testsite/make_select_options_paytype.html', context={'select_list': currency_types_for_form})

def load_pay_type_buy(request):
    currency_to_buy = request.GET.get('Currency_to_buy')
    currency_types = list(set(ExchangeID.objects.filter(ReceiveCurrencyISO=currency_to_buy).values_list("ReceiveTransferType", flat=True)))
    currency_types_for_form = []
    if 'CRP' in currency_types:
        currency_types_for_form.append('Перевод по сети блокчейн')
    if 'CSH' in currency_types:
        currency_types_for_form.append('Наличные')
    if 'CRD' in currency_types:
        currency_types_for_form.append('Карточный перевод')
    currency_types_for_form.sort()
    return render(request, 'testsite/make_select_options_paytype.html', context={'select_list': currency_types_for_form})

def load_payment_method_from(request):
    Pay_type_sell = request.GET.get('Pay_type_sell')
    Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
    if Pay_type_sell == 'Карточный перевод':
        FinOfficeFrom = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
    elif Pay_type_sell == 'Наличные':
        FinOfficeFrom = list(Currency_source.objects.filter(FinOfficeFrom__in = list(FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
    elif Pay_type_sell == 'Перевод по сети блокчейн':
        FinOfficeFrom = []

        FinOfficeFromTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeFrom__in=list(FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
        # FinOfficeFrom.append(" - Криптобиржи")
        for finoffice in FinOfficeFromTypes_Crypto_Exchange:
            FinOfficeFrom.append(finoffice)

        FinOfficeFromTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeFrom__in=list(FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
        # FinOfficeFrom.append(" - Криптокошельки")
        for finoffice in FinOfficeFromTypes_Crypto_Wallet:
            FinOfficeFrom.append(finoffice)

    return render(request, 'testsite/make_select_options_finoffice.html', context={'select_list': FinOfficeFrom})

def load_payment_method_to(request):
    Pay_type_buy = request.GET.get('Pay_type_buy')
    Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
    if Pay_type_buy == 'Карточный перевод':
        FinOfficeTo = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
    elif Pay_type_buy == 'Наличные':
        FinOfficeTo = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
    elif Pay_type_buy == 'Перевод по сети блокчейн':
        FinOfficeTo = []
        FinOfficeToTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
        # FinOfficeTo.append(" - Криптобиржи")
        for finoffice in FinOfficeToTypes_Crypto_Exchange:
            FinOfficeTo.append(finoffice)

        FinOfficeToTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
        # FinOfficeTo.append(" - Криптокошельки")
        for finoffice in FinOfficeToTypes_Crypto_Wallet:
            FinOfficeTo.append(finoffice)

    return render(request, 'testsite/make_select_options_finoffice.html', context={'select_list': FinOfficeTo})

def load_pay_type_sell_num(request, num):
    currency_to_sell = request.GET.get('Currency_to_sell')
    currency_types = list(set(ExchangeID.objects.filter(SendCurrencyISO=currency_to_sell).values_list("SendTransferType",flat=True)))
    currency_types_for_form = []
    if 'CRP' in currency_types:
        currency_types_for_form.append('Перевод по сети блокчейн')
    if 'CSH' in currency_types:
        currency_types_for_form.append('Наличные')
    if 'CRD' in currency_types:
        currency_types_for_form.append('Карточный перевод')
    currency_types_for_form.sort()
    return render(request, 'testsite/make_select_options_paytype.html', context={'select_list': currency_types_for_form})

def load_pay_type_buy_num(request, num):
    currency_to_buy = request.GET.get('Currency_to_buy')
    currency_types = list(set(ExchangeID.objects.filter(ReceiveCurrencyISO=currency_to_buy).values_list("ReceiveTransferType", flat=True)))
    currency_types_for_form = []
    if 'CRP' in currency_types:
        currency_types_for_form.append('Перевод по сети блокчейн')
    if 'CSH' in currency_types:
        currency_types_for_form.append('Наличные')
    if 'CRD' in currency_types:
        currency_types_for_form.append('Карточный перевод')
    currency_types_for_form.sort()
    return render(request, 'testsite/make_select_options_paytype.html', context={'select_list': currency_types_for_form})

def load_payment_method_from_num(request, num):
    Pay_type_sell = request.GET.get('Pay_type_sell')
    Pay_type_sell = urllib.parse.unquote(Pay_type_sell)
    if Pay_type_sell == 'Карточный перевод':
        FinOfficeFrom = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
            FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by(
                'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
    elif Pay_type_sell == 'Наличные':
        FinOfficeFrom = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
            FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by(
                'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
    elif Pay_type_sell == 'Перевод по сети блокчейн':
        FinOfficeFrom = []

        FinOfficeFromTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
            FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS",
                                                                                          flat=True).order_by(
                'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
        # FinOfficeFrom.append(" - Криптобиржи")
        for finoffice in FinOfficeFromTypes_Crypto_Exchange:
            FinOfficeFrom.append(finoffice)

        FinOfficeFromTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeFrom__in=list(
            FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS",
                                                                                             flat=True).order_by(
                'Name_RUS'))).values_list('FinOfficeFrom', flat=True).order_by('FinOfficeFrom').distinct())
        # FinOfficeFrom.append(" - Криптокошельки")
        for finoffice in FinOfficeFromTypes_Crypto_Wallet:
            FinOfficeFrom.append(finoffice)

    return render(request, 'testsite/make_select_options_finoffice.html', context={'select_list': FinOfficeFrom})

def load_payment_method_to_num(request, num):
    Pay_type_buy = request.GET.get('Pay_type_buy')
    Pay_type_buy = urllib.parse.unquote(Pay_type_buy)
    if Pay_type_buy == 'Карточный перевод':
        FinOfficeTo = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Банки").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
    elif Pay_type_buy == 'Наличные':
        FinOfficeTo = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Наличные").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
    elif Pay_type_buy == 'Перевод по сети блокчейн':
        FinOfficeTo = []
        FinOfficeToTypes_Crypto_Exchange = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптобиржи-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
        # FinOfficeTo.append(" - Криптобиржи")
        for finoffice in FinOfficeToTypes_Crypto_Exchange:
            FinOfficeTo.append(finoffice)

        FinOfficeToTypes_Crypto_Wallet = list(Currency_source.objects.filter(FinOfficeTo__in=list(FinOffice.objects.filter(FinOfficeType="Криптокошельки-Отправители").values_list("Name_RUS", flat=True).order_by('Name_RUS'))).values_list('FinOfficeTo', flat=True).order_by('FinOfficeTo').distinct())
        # FinOfficeTo.append(" - Криптокошельки")
        for finoffice in FinOfficeToTypes_Crypto_Wallet:
            FinOfficeTo.append(finoffice)

    return render(request, 'testsite/make_select_options_finoffice.html', context={'select_list': FinOfficeTo})

#
def P2Pmarket_Exchange_order(request):
    # global user_type
    # user_type = cache.get('user_type')
    # ExchangeName = cache.get('ExchangeName')
    user = Users.objects.get(TG_Contact=request.user)
    Country = Countries.objects.filter(Country_code=user.COUNTRY).values('Name_RUS')[0]['Name_RUS']
    Date = datetime.now().date()
    form = Exchangeorder(request.user)

    return render(request, 'testsite/P2Pmarket_Exchange_order.html',
                  {'form': form, 'title': 'Заявка на обмен', 'error': "", 'Country': Country, 'Date': Date,
                   'balance': user.balanceFull, 'param': 0})

#
def P2Pmarket_Exchange_order_confirm(request):
    # global RequestInfo, user_type
    # user_type = cache.get('user_type')
    user = Users.objects.get(TG_Contact=request.user)
    Country = Countries.objects.filter(Country_code=user.COUNTRY).values('Name_RUS')[0]['Name_RUS']
    Date = datetime.now().date()
    form = Exchangeorder(request.user, request.POST)
    RequestInfo = {}
    #print(form.errors)
    if form.is_valid():
        param = 0
        error = ""
        error2 = ""
        error3 = ""
        error4 = ""
        error5 = ""

        if str(request.POST.get("DeliveryType")) == 'None':
            param += 1
            error = "Не выбран способ доставки"

        if "-" in str(form.cleaned_data.get("FinOfficeFrom")):
            param += 1
            error3 = "Выбран некорректный метод оплаты"

        current_datetime = datetime.now().date()
        tomorrow = current_datetime + timedelta(days=1)
        current_hour = int(time.localtime()[3])
        chosen_hour = int(str(form.cleaned_data.get("Order_time"))[:str(form.cleaned_data.get("Order_time")).find(":")])
        if current_hour > chosen_hour:
            current_datetime = tomorrow

        if form.cleaned_data.get("Currency_to_sell") != "-" and form.cleaned_data.get("Currency_to_buy") != "-":
            p_t_b = ""
            p_t_s = ""
            if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                p_t_b = "CSH"
            elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                p_t_b = "CRP"
            elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                p_t_b = "CRD"

            if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                p_t_s = "CSH"
            elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                p_t_s = "CRP"
            elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                p_t_s = "CRD"

            exchange = ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                    SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                    ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy"))).all()
            if len(exchange) == 0:
                param += 1
                error5 = "Данная валютная пара недоступна к обмену"
                ID = ''
            else:
                ID = ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                          SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                          ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy"))).values_list('pk', flat=True)[0]

            if form.cleaned_data.get('Send_or_Receive') == 'Кол-во актива к покупке':
                s_r = 'receive'
            elif form.cleaned_data.get('Send_or_Receive') == 'Кол-во контрактива к продаже':
                s_r = 'send'

        if param != 0:
            return render(request, 'testsite/P2Pmarket_Exchange_order.html',
                          {'form': form, 'title': 'Заявка на обмен', 'error': error, 'error2': error2, 'error3': error3,
                           'error4': error4, 'error5': error5, 'Country': Country, 'Date': Date, 'param': 0})
        else:
            RequestInfo["Currency_to_sell"] = form.cleaned_data.get("Currency_to_sell")
            RequestInfo["Currency_to_buy"] = form.cleaned_data.get("Currency_to_buy")
            RequestInfo["PriceType"] = form.cleaned_data.get("PriceType")
            RequestInfo["Pay_type_sell"] = form.cleaned_data.get("Pay_type_sell")
            RequestInfo["FinOfficeFrom"] = form.cleaned_data.get("FinOfficeFrom")
            RequestInfo["Pay_type_buy"] = form.cleaned_data.get("Pay_type_buy")
            RequestInfo["FinOfficeTo"] = form.cleaned_data.get("FinOfficeTo")
            RequestInfo["COUNTRY"] = Countries.objects.filter(Country_code=user.COUNTRY).values('Name_RUS')[0][
                'Name_RUS']
            RequestInfo["CITY"] = form.cleaned_data.get("CITY")
            RequestInfo["Order_day"] = current_datetime
            RequestInfo["Order_time"] = form.cleaned_data.get("Order_time")
            RequestInfo["DeliveryType"] = '; '.join(form.cleaned_data.get("DeliveryType"))
            RequestInfo['Send_or_Receive'] = s_r
            RequestInfo["Order_amount"] = form.cleaned_data.get("Order_amount")
            RequestInfo["Limit_amount"] = form.cleaned_data.get("Limit_amount")
            RequestInfo["ID"] = ID
            RequestInfo["p_t_b"] = p_t_b
            RequestInfo["p_t_s"] = p_t_s
            RequestInfo["Comment"] = form.cleaned_data.get("Comment")
            cache.set('RequestInfo', RequestInfo)
            return render(request, 'testsite/P2Pmarket_Exchange_order_confirm.html',
                          {'title': 'Подтверждение заявки на обмен', 'RequestInfo': RequestInfo})

#
def P2Pmarket_Exchange_order_final(request):
    # global RequestInfo, user_type
    # user_type = cache.get('user_type')
    RequestInfo = cache.get('RequestInfo')
    current_datetime = datetime.now().date()
    tomorrow = current_datetime + timedelta(days=1)
    current_hour = int(time.localtime()[3])
    chosen_hour = int(str(RequestInfo['Order_time'])[:str(RequestInfo['Order_time']).find(":")])
    if current_hour > chosen_hour:
        current_datetime = tomorrow
    city = Cities.objects.filter(Name_RUS=RequestInfo["CITY"]).values('City_code', 'Country')
    user = Users.objects.get(TG_Contact=request.user)
    if RequestInfo["Send_or_Receive"] == 'send':
        Orders.objects.create(TG_Contact=request.user, ExchangeID=RequestInfo['ID'], PriceType=RequestInfo['PriceType'],
                              SendCurrencyISO=RequestInfo['Currency_to_sell'],
                              ReceiveCurrencyISO=RequestInfo['Currency_to_buy'],
                              SendTransferType=RequestInfo['p_t_s'], ReceiveTransferType=RequestInfo['p_t_b'],
                              SendAmount=RequestInfo['Order_amount'], FinOfficeFrom=RequestInfo['FinOfficeFrom'],
                              FinOfficeTo=RequestInfo['FinOfficeTo'],
                              OrderDate=current_datetime, TimeInterval=RequestInfo['Order_time'], Country=user.COUNTRY,
                              City=city[0]['City_code'], DeliveryType=RequestInfo["DeliveryType"],
                              OrderLimit=RequestInfo["Limit_amount"], Comment=RequestInfo["Comment"])
    elif RequestInfo["Send_or_Receive"] == 'receive':
        Orders.objects.create(TG_Contact=request.user, ExchangeID=RequestInfo['ID'], PriceType=RequestInfo['PriceType'],
                              SendCurrencyISO=RequestInfo['Currency_to_sell'],
                              ReceiveCurrencyISO=RequestInfo['Currency_to_buy'],
                              SendTransferType=RequestInfo['p_t_s'], ReceiveTransferType=RequestInfo['p_t_b'],
                              ReceiveAmount=RequestInfo['Order_amount'], FinOfficeFrom=RequestInfo['FinOfficeFrom'],
                              FinOfficeTo=RequestInfo['FinOfficeTo'],
                              OrderDate=current_datetime, TimeInterval=RequestInfo['Order_time'], Country=user.COUNTRY,
                              City=city[0]['City_code'], DeliveryType=RequestInfo["DeliveryType"],
                              OrderLimit=RequestInfo["Limit_amount"], Comment=RequestInfo["Comment"])
    # order = Orders.objects.get(TG_Contact=request.user, ExchangeID=RequestInfo['ID'], PriceType=RequestInfo['PriceType'],
    #                       SendCurrencyISO=RequestInfo['Currency_to_sell'],
    #                       ReceiveCurrencyISO=RequestInfo['Currency_to_buy'],
    #                       SendTransferType=RequestInfo['p_t_s'], ReceiveTransferType=RequestInfo['p_t_b'],
    #                       SendAmount=RequestInfo['Order_amount'], ReceiveAmount=RequestInfo['Order_amount'] * 1,
    #                       FinOfficeFrom=RequestInfo['FinOfficeFrom'], OrderDate=current_datetime,
    #                       TimeInterval=RequestInfo['Order_time'], Country=user.COUNTRY,
    #                       City=city[0]['City_code'], DeliveryType=RequestInfo["DeliveryType"],
    #                       OrderLimit=RequestInfo["Limit_amount"], Comment=RequestInfo["Comment"])
    # order.RequestID = order.pk
    # order.save()
    cache.delete('RequestInfo')
    return redirect("P2Pmarket")

#
def P2Pmarket_change_Exchange_order(request, num):
    # global RequestInfo, user_type
    # user_type = cache.get('user_type')
    user = Users.objects.get(TG_Contact=request.user)
    Country = Countries.objects.filter(Country_code=user.COUNTRY).values('Name_RUS')[0]['Name_RUS']
    Date = datetime.now().date()
    if request.method == 'POST':
        change_list = []
        form = Changeexchangeorder(request.user, request.POST)
        if form.is_valid():
            param = 0
            error = ""
            error2 = ""
            error3 = ""
            error4 = ""
            error5 = ""

            if str(request.POST.get("DeliveryType")) == 'None':
                param += 1
                error = "Не выбран способ доставки"

            if "-" in str(form.cleaned_data.get("FinOfficeFrom")):
                param += 1
                error3 = "Выбран некорректный метод оплаты отдаваемой валюты"

            if "-" in str(form.cleaned_data.get("FinOfficeTo")):
                param += 1
                error4 = "Выбран некорректный метод оплаты получаемой валюты"

            current_datetime = datetime.now().date()
            tomorrow = current_datetime + timedelta(days=1)
            current_hour = int(time.localtime()[3])
            chosen_hour = int(
                str(form.cleaned_data.get("Order_time"))[:str(form.cleaned_data.get("Order_time")).find(":")])
            if current_hour > chosen_hour:
                current_datetime = tomorrow

            if form.cleaned_data.get("Currency_to_sell") != "-" and form.cleaned_data.get("Currency_to_buy") != "-":
                p_t_b = ""
                p_t_s = ""
                if form.cleaned_data.get("Pay_type_buy") == "Наличные":
                    p_t_b = "CSH"
                elif form.cleaned_data.get("Pay_type_buy") == "Перевод по сети блокчейн":
                    p_t_b = "CRP"
                elif form.cleaned_data.get("Pay_type_buy") == "Карточный перевод":
                    p_t_b = "CRD"

                if form.cleaned_data.get("Pay_type_sell") == "Наличные":
                    p_t_s = "CSH"
                elif form.cleaned_data.get("Pay_type_sell") == "Перевод по сети блокчейн":
                    p_t_s = "CRP"
                elif form.cleaned_data.get("Pay_type_sell") == "Карточный перевод":
                    p_t_s = "CRD"
                exchange = ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                     SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                     ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy"))).all()
                if len(exchange) == 0:
                    param += 1
                    error5 = "Данная валютная пара недоступна к обмену"
                    ID = ''
                else:
                    ID = ExchangeID.objects.filter(SendTransferType=p_t_s, ReceiveTransferType=p_t_b,
                                                   SendCurrencyISO=str(form.cleaned_data.get("Currency_to_sell")),
                                                   ReceiveCurrencyISO=str(form.cleaned_data.get("Currency_to_buy"))).values_list(
                                                                                                    'pk', flat=True)[0]

            if param != 0:
                return render(request, 'testsite/P2Pmarket_Exchange_order.html',
                              {'form': form, 'title': 'Заявка на обмен', 'error': error, 'error2': error2,
                               'error3': error3,
                               'error4': error4, 'error5': error5, 'Country': Country, 'Date': Date,
                               'balance': user.balanceFull, 'param': 1, 'num': num})
            else:
                order = Orders.objects.get(pk=num)
                if int(order.ExchangeID) != int(ID):
                    Requests_data = Requests.objects.filter(OrderID=order.pk).values('pk', 'PCCNTR', 'ExchangePointID')
                    for request_data in Requests_data:
                        # print('ID - ' + str(ID))
                        # print('ID_List - ' + str(list(EP_ExchangeID.objects.filter(PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID']).values_list('ExchangeTransferID', flat=True))))
                        if str(ID) not in list(EP_ExchangeID.objects.filter(PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID']).values_list('ExchangeTransferID', flat=True)):
                            Requests.objects.filter(OrderID=order.pk, PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID']).delete()
                            DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                       OrderID=order.pk,
                                                                       RequestID=request_data['pk'])
                            PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                            PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                            DealReserve.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                    OrderID=order.pk,
                                                    RequestID=request_data['pk']).delete()
                            PCCNTR_data.save()
                            partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],ContactType='PART')
                            Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                                         PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                         Text='Предложение по заявке на обмен №' + str(order.pk) + ' было отменено по причине смены направления обмена, которое не зарегистрировано в обменнике ')
                            mail_subject = 'Изменения в заявке на обмен'
                            email = \
                            User.objects.filter(username=partner_contacts.TG_Contact).values_list('email', flat=True)[0]
                            to_email = email
                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                            html_content = get_template(
                                'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                'user': partner_contacts.TG_Contact,
                                'OrderNum': order.pk,
                            })
                            msg.attach_alternative(html_content, "text/html")
                            res = msg.send()

                            org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'], ContactType='ORG',
                                                                    ExchangePointID__contains=request_data[
                                                                        'ExchangePointID'])
                            if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                                Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                             PCCNTR=request_data['PCCNTR'],
                                                             ExchangePointID=request_data['ExchangePointID'],
                                                             Text='Предложение по заявке на обмен №' + str(
                                                                 order.pk) + ' было отменено по причине смены направления обмена, которое не зарегистрировано в обменнике ')
                                mail_subject = 'Изменения в заявке на обмен'
                                email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email',flat=True)[0]
                                to_email = email
                                msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                html_content = get_template(
                                    'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                    'user': org_contacts.TG_Contact,
                                    'OrderNum': order.pk,
                                })
                                msg.attach_alternative(html_content, "text/html")
                                res = msg.send()

                            job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                            empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                                        ContactType__in=job_positions,
                                                                        ExchangePointID__contains=request_data[
                                                                            'ExchangePointID']).values('TG_Contact',
                                                                                                       'ContactType')
                            for empl in empl_contacts:
                                if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                                    'TG_Contact'] != org_contacts.TG_Contact:
                                    Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                                                 ContactType=empl['ContactType'],
                                                                 PCCNTR=request_data['PCCNTR'],
                                                                 ExchangePointID=request_data['ExchangePointID'],
                                                                 Text='Предложение по заявке на обмен №' + str(
                                                                     order.pk) + ' было отменено по причине смены направления обмена, которое не зарегистрировано в обменнике ')
                                    mail_subject = 'Изменения в заявке на обмен'
                                    email = User.objects.filter(username=empl['TG_Contact']).values_list('email',flat=True)[ 0]
                                    to_email = email
                                    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                    html_content = get_template(
                                        'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                        'user': empl['TG_Contact'],
                                        'OrderNum': order.pk,
                                    })
                                    msg.attach_alternative(html_content, "text/html")
                                    res = msg.send()

                    change_list.append('Направление обмена: ' + str(ExchangeID.objects.filter(pk=order.ExchangeID).values_list('Name_RUS', flat=True)[0]) + ' -> ' + str(ExchangeID.objects.filter(pk=ID).values_list('Name_RUS', flat=True)[0]))
                    order.ExchangeID = ID
                    param_exchange = 1
                else:
                    param_exchange = 0

                if order.PriceType != form.cleaned_data.get("PriceType"):
                    change_list.append('Тип цены: ' + str(order.PriceType) + ' -> ' + str(form.cleaned_data.get("PriceType")))
                    order.PriceType = form.cleaned_data.get("PriceType")
                    param_pricetype = 1
                else:
                    param_pricetype = 0

                if order.ReceiveCurrencyISO != form.cleaned_data.get("Currency_to_buy"):
                    change_list.append('Актив к покупке: ' + str(order.ReceiveCurrencyISO) + ' -> ' + str(form.cleaned_data.get("Currency_to_buy")))
                    order.ReceiveCurrencyISO = form.cleaned_data.get("Currency_to_buy")

                if order.SendCurrencyISO != form.cleaned_data.get("Currency_to_sell"):
                    change_list.append('Контрактив к продаже: ' + str(order.SendCurrencyISO) + ' -> ' + str(form.cleaned_data.get("Currency_to_sell")))
                    order.SendCurrencyISO = form.cleaned_data.get("Currency_to_sell")

                if order.SendTransferType != p_t_s:
                    if str(order.SendTransferType) == "CSH":
                        p_t_b2 = "Наличные"
                    elif str(order.SendTransferType) == "CRP":
                        p_t_b2 = "Перевод по сети блокчейн"
                    elif str(order.SendTransferType) == "CRD":
                        p_t_b2 = "Карточный перевод"

                    change_list.append('Тип перевода отдаваемой валюты: ' + p_t_b2 + ' -> ' + form.cleaned_data.get("Pay_type_sell"))
                    order.SendTransferType = p_t_s
                if order.ReceiveTransferType != p_t_b:
                    if str(order.ReceiveTransferType) == "CSH":
                        p_t_s2 = "Наличные"
                    elif str(order.ReceiveTransferType) == "CRP":
                        p_t_s2 = "Перевод по сети блокчейн"
                    elif str(order.ReceiveTransferType) == "CRD":
                        p_t_s2 = "Карточный перевод"
                        
                    change_list.append('Тип перевода получаемой валюты: ' + p_t_s2 + ' -> ' + form.cleaned_data.get("Pay_type_buy"))
                    order.ReceiveTransferType = p_t_b

                param_finoffice=0
                if order.FinOfficeFrom != form.cleaned_data.get("FinOfficeFrom"):
                    change_list.append('Метод оплаты отдаваемой валюты: ' + str(order.FinOfficeFrom) + ' -> ' + str(form.cleaned_data.get("FinOfficeFrom")))
                    order.FinOfficeFrom = form.cleaned_data.get("FinOfficeFrom")
                    param_finoffice+=1

                if order.FinOfficeTo != form.cleaned_data.get("FinOfficeTo"):
                    change_list.append('Метод оплаты получаемой валюты: ' + str(order.FinOfficeTo) + ' -> ' + str(form.cleaned_data.get("FinOfficeTo")))
                    order.FinOfficeTo = form.cleaned_data.get("FinOfficeTo")
                    param_finoffice+=1


                if form.cleaned_data.get('Send_or_Receive') == 'Кол-во актива к покупке': # Пропускаем в конец
                    if order.ReceiveAmount != form.cleaned_data.get("Order_amount") or param_exchange==1 or param_pricetype==1 or param_finoffice!=0:
                        order.ReceiveAmount = form.cleaned_data.get("Order_amount")
                        Requests_data = Requests.objects.filter(OrderID=order.pk).values('pk', 'PCCNTR', 'ExchangePointID')
                        if len(Requests_data) != 0:
                            for request_data in Requests_data:
                                full_request = Requests.objects.get(OrderID=order.pk, PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID'])
                                opertype = ExchangeID.objects.filter(pk=order.ExchangeID).values_list('OperTypes', flat=True)[0]
                                OPRTs = []
                                if ';' in opertype:
                                    while ';' in opertype:
                                        oprt = opertype[:opertype.find(";")].strip()
                                        OPRTs.append(oprt)
                                        opertype = opertype[opertype.find(";") + 1:].strip()
                                    OPRTs.append(opertype.strip())
                                else:
                                    OPRTs.append(opertype.strip())
                                if len(OPRTs) == 1:
                                    currency_value = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                          FinOfficeFrom=order.FinOfficeFrom,
                                                                                          FinOfficeTo=order.FinOfficeTo,
                                                                                          QuotesRC=
                                                                                          PCCNTR_OperTypes.objects.filter(
                                                                                              PCCNTR=request_data['PCCNTR'],
                                                                                              OperType=OPRTs[
                                                                                                  0]).values_list(
                                                                                              'QuotesRC',
                                                                                              flat=True)[
                                                                                              0]).values_list(
                                        'Value', flat=True)[0])
                                    exchange_rate = currency_value
                                elif len(OPRTs) == 2:
                                    currency_value_1 = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                            FinOfficeFrom=order.FinOfficeFrom,
                                                                                            FinOfficeTo='TRC20',
                                                                                            QuotesRC=
                                                                                            PCCNTR_OperTypes.objects.filter(
                                                                                                PCCNTR=request_data['PCCNTR'],
                                                                                                OperType=OPRTs[0]).values_list(
                                                                                                'QuotesRC',
                                                                                                flat=True)[
                                                                                                0]).values_list(
                                        'Value', flat=True)[
                                                                 0])
                                    currency_value_2 = float(Currency_source.objects.filter(OperType=OPRTs[1],
                                                                                            FinOfficeFrom='TRC20',
                                                                                            FinOfficeTo=order.FinOfficeTo,
                                                                                            QuotesRC=
                                                                                            PCCNTR_OperTypes.objects.filter(
                                                                                                PCCNTR=request_data['PCCNTR'],
                                                                                                OperType=OPRTs[
                                                                                                    0]).values_list(
                                                                                                'QuotesRC',
                                                                                                flat=True)[
                                                                                                0]).values_list(
                                        'Value', flat=True)[
                                                                 0])
                                    exchange_rate = round(currency_value_1 * currency_value_2, 5)
                                # Добавить проверку на минимальный и максимальный размер обмена - если вне рамок, то деактивируем предложение
                                profit_norm = EP_ExchangeID.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                        ExchangePointID=request_data['ExchangePointID'],
                                                                        ExchangeTransferID=order.ExchangeID)
                                # print(exchange_rate)
                                # print(order.ReceiveAmount)
                                # print(profit_norm.ExchTOAmount_Min)
                                # print(profit_norm.ExchTOAmount_Max)
                                if order.ReceiveAmount < profit_norm.ExchTOAmount_Min and order.ReceiveAmount > profit_norm.ExchTOAmount_Max:
                                    Requests.objects.filter(OrderID=order.pk, PCCNTR=request_data['PCCNTR'],ExchangePointID=request_data['ExchangePointID']).delete()
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                               OrderID=order.pk,
                                                               RequestID=request_data['pk']).delete()
                                    PCCNTR_data.save()

                                    partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType='PART')
                                    Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                                                 PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                                 Text='Предложение по заявке на обмен №' + str(
                                                                     order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                    mail_subject = 'Изменения в заявке на обмен'
                                    email = \
                                        User.objects.filter(username=partner_contacts.TG_Contact).values_list('email',
                                                                                                              flat=True)[0]
                                    to_email = email
                                    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                    html_content = get_template(
                                        'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                        'user': partner_contacts.TG_Contact,
                                        'OrderNum': order.pk,
                                    })
                                    msg.attach_alternative(html_content, "text/html")
                                    res = msg.send()

                                    org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                            ContactType='ORG',
                                                                            ExchangePointID__contains=request_data[
                                                                                'ExchangePointID'])
                                    if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                                        Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                                     PCCNTR=request_data['PCCNTR'],
                                                                     ExchangePointID=request_data['ExchangePointID'],
                                                                     Text='Предложение по заявке на обмен №' + str(
                                                                         order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                        mail_subject = 'Изменения в заявке на обмен'
                                        email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email',
                                                                                                                  flat=True)[
                                            0]
                                        to_email = email
                                        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                        html_content = get_template(
                                            'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                            'user': org_contacts.TG_Contact,
                                            'OrderNum': order.pk,
                                        })
                                        msg.attach_alternative(html_content, "text/html")
                                        res = msg.send()

                                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                                    empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType__in=job_positions,
                                                                                ExchangePointID__contains=request_data[
                                                                                    'ExchangePointID']).values('TG_Contact',
                                                                                                               'ContactType')
                                    for empl in empl_contacts:
                                        if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                                            'TG_Contact'] != org_contacts.TG_Contact:
                                            Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                                                         ContactType=empl['ContactType'],
                                                                         PCCNTR=request_data['PCCNTR'],
                                                                         ExchangePointID=request_data['ExchangePointID'],
                                                                         Text='Предложение по заявке на обмен №' + str(
                                                                             order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                            mail_subject = 'Изменения в заявке на обмен'
                                            email = User.objects.filter(username=empl['TG_Contact']).values_list('email',
                                                                                                                 flat=True)[
                                                0]
                                            to_email = email
                                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                            html_content = get_template(
                                                'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                                'user': empl['TG_Contact'],
                                                'OrderNum': order.pk,
                                            })
                                            msg.attach_alternative(html_content, "text/html")
                                            res = msg.send()


                                    continue
                                elif order.PriceType == 'Плавающая' or param_exchange==1 or param_pricetype==1 or param_finoffice!=0:
                                    Norm_Prib = profit_norm.EP_PRFTNORM
                                    Norm_Prib_Name_1 = []
                                    Norm_Prib_Name_2 = []
                                    Norm_Prib_Percent = []
                                    if ';' in Norm_Prib:
                                        while ";" in Norm_Prib:
                                            N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
                                            Name = N_P[:N_P.find(' ')].strip()
                                            Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
                                            Name_1 = Name[:Name.find("-")].strip()
                                            Norm_Prib_Name_1.append(Name_1)
                                            Name_2 = Name[Name.find("-") + 1:].strip()
                                            Norm_Prib_Name_2.append(Name_2)
                                            Norm_Prib_Percent.append(Percent)
                                            Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
                                        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                                        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                                        Name_1 = Name[:Name.find("-")].strip()
                                        Norm_Prib_Name_1.append(Name_1)
                                        Name_2 = Name[Name.find("-") + 1:].strip()
                                        Norm_Prib_Name_2.append(Name_2)
                                        Norm_Prib_Percent.append(Percent)
                                    else:
                                        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                                        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                                        Name_1 = Name[:Name.find("-")].strip()
                                        Norm_Prib_Name_1.append(Name_1)
                                        Name_2 = Name[Name.find("-") + 1:].strip()
                                        Norm_Prib_Name_2.append(Name_2)
                                        Norm_Prib_Percent.append(Percent)

                                    for i in range(len(Norm_Prib_Name_1)):
                                        if order.ReceiveAmount >= float(Norm_Prib_Name_1[i]) and order.ReceiveAmount <= float(Norm_Prib_Name_2[i]):
                                            max_percent_new = float(Norm_Prib_Percent[i])

                                    exch_rate = round(exchange_rate * (1 - max_percent_new / 100),5)
                                    # print(exch_rate)
                                    full_request.SendAmount = round(order.ReceiveAmount / exch_rate,2)
                                    full_request.ReceiveAmount = order.ReceiveAmount
                                else:
                                    # Дописать перерасчет получаемой суммы зная курс в таблице Requests
                                    exch_rate = round(full_request.ReceiveAmount / full_request.SendAmount,5)
                                    # print(exch_rate)
                                    full_request.SendAmount = round(order.ReceiveAmount / exch_rate,2)
                                    full_request.ReceiveAmount = order.ReceiveAmount

                                # Cчитаем отдаваемую и получаемую сумму в USDT (дописать поиск получаемой суммы)
                                if form.cleaned_data.get("Currency_to_sell") != 'USDT' and form.cleaned_data.get("Currency_to_buy") != 'USDT':
                                    sumusdt_send = int(full_request.SendAmount * float(
                                        Currency_source.objects.get(OperType=str(form.cleaned_data.get("Currency_to_sell")) + " => USDT",
                                                                    FinOfficeFrom='Наличные',
                                                                    FinOfficeTo='TRC20',
                                                                    QuotesRC='GARALL').Value))
                                    sumusdt_receive = int(full_request.ReceiveAmount * float(
                                        Currency_source.objects.get(OperType=str(form.cleaned_data.get("Currency_to_buy")) + " => USDT",
                                                                    FinOfficeFrom='Наличные',
                                                                    FinOfficeTo='TRC20',
                                                                    QuotesRC='GARALL').Value))
                                elif form.cleaned_data.get("Currency_to_sell") == 'USDT':
                                    sumusdt_send = int(full_request.SendAmount)
                                    sumusdt_receive = int(full_request.SendAmount)
                                else:
                                    sumusdt_send = int(full_request.ReceiveAmount)
                                    sumusdt_receive = int(full_request.ReceiveAmount)

                                # Cчитаем отдаваемую и получаемую сумму в EUR (дописать поиск получаемой суммы)
                                if form.cleaned_data.get("Currency_to_sell") != 'EUR' and form.cleaned_data.get("Currency_to_buy") != 'EUR':
                                    sumeur_send = int(sumusdt_send * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                                       FinOfficeFrom='TRC20',
                                                                                                       FinOfficeTo='Наличные',
                                                                                                       QuotesRC='GARALL').Value))
                                    sumeur_receive = int(
                                        sumusdt_receive * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                            FinOfficeFrom='TRC20',
                                                                                            FinOfficeTo='Наличные',
                                                                                            QuotesRC='GARALL').Value))
                                elif form.cleaned_data.get("Currency_to_sell") == 'EUR':
                                    sumeur_send = int(full_request.SendAmount)
                                    sumeur_receive = int(full_request.SendAmount)
                                else:
                                    sumeur_send = int(full_request.ReceiveAmount)
                                    sumeur_receive = int(full_request.ReceiveAmount)

                                balance_amount = float(PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR']).Balance) - float(PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR']).Reserve) + float(DealReserve.objects.get(PCCNTR=request_data['PCCNTR'], OrderID=order.pk, RequestID=request_data['pk']).Reserve_Amount)
                                # print(balance_amount)

                                # Проверка на баланс обменника (хватает ли денег на комиссию в случае изменения стоимости обмена)
                                if int(sumusdt_receive * 0.01) > balance_amount:
                                    Requests.objects.filter(OrderID=order.pk, PCCNTR=request_data['PCCNTR'],ExchangePointID=request_data['ExchangePointID']).delete()
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                               OrderID=order.pk,
                                                               RequestID=request_data['pk']).delete()
                                    PCCNTR_data.save()

                                    partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType='PART')
                                    Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                                                 PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                                 Text='Предложение по заявке на обмен №' + str(
                                                                     order.pk) + ' была отменена по причине недостатка средств для оплаты комиссии платформы')
                                    mail_subject = 'Изменения в заявке на обмен'
                                    email = \
                                        User.objects.filter(username=partner_contacts.TG_Contact).values_list('email',
                                                                                                              flat=True)[0]
                                    to_email = email
                                    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                    html_content = get_template(
                                        'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                        'user': partner_contacts.TG_Contact,
                                        'OrderNum': order.pk,
                                    })
                                    msg.attach_alternative(html_content, "text/html")
                                    res = msg.send()

                                    org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                            ContactType='ORG',
                                                                            ExchangePointID__contains=request_data[
                                                                                'ExchangePointID'])
                                    if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                                        Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                                     PCCNTR=request_data['PCCNTR'],
                                                                     ExchangePointID=request_data['ExchangePointID'],
                                                                     Text='Предложение по заявке на обмен №' + str(
                                                                         order.pk) + ' была отменена по причине недостатка средств для оплаты комиссии платформы')
                                        mail_subject = 'Изменения в заявке на обмен'
                                        email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email',
                                                                                                                  flat=True)[
                                            0]
                                        to_email = email
                                        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                        html_content = get_template(
                                            'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                            'user': org_contacts.TG_Contact,
                                            'OrderNum': order.pk,
                                        })
                                        msg.attach_alternative(html_content, "text/html")
                                        res = msg.send()

                                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                                    empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType__in=job_positions,
                                                                                ExchangePointID__contains=request_data[
                                                                                    'ExchangePointID']).values('TG_Contact',
                                                                                                               'ContactType')
                                    for empl in empl_contacts:
                                        if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                                            'TG_Contact'] != org_contacts.TG_Contact:
                                            Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                                                         ContactType=empl['ContactType'],
                                                                         PCCNTR=request_data['PCCNTR'],
                                                                         ExchangePointID=request_data['ExchangePointID'],
                                                                         Text='Предложение по заявке на обмен №' + str(
                                                                             order.pk) + ' была отменена по причине недостатка средств для оплаты комиссии платформы')
                                            mail_subject = 'Изменения в заявке на обмен'
                                            email = User.objects.filter(username=empl['TG_Contact']).values_list('email',
                                                                                                                 flat=True)[
                                                0]
                                            to_email = email
                                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                            html_content = get_template(
                                                'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                                'user': empl['TG_Contact'],
                                                'OrderNum': order.pk,
                                            })
                                            msg.attach_alternative(html_content, "text/html")
                                            res = msg.send()

                                    continue
                                else:
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    # old_reserve = DealReserve_data.Reserve_Amount
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve_data.Reserve_Amount = int(sumusdt_receive * 0.01)
                                    # new_reserve = int(sumusdt_receive * 0.01)
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve + DealReserve_data.Reserve_Amount
                                    DealReserve_data.save()
                                    PCCNTR_data.save()

                                full_request.ExchRateEURUSDT = round(sumusdt_receive / sumeur_send, 5)
                                full_request.ExchRateUSDTEUR = round(sumeur_receive / sumusdt_send, 5)
                                full_request.sendinEUR = sumeur_send
                                full_request.receiveinEUR = sumeur_receive
                                full_request.sendinUSDT = sumusdt_send
                                full_request.receiveinUSDT = sumusdt_receive

                                full_request.save()

                            if order.SendAmount is None:
                                change_list.append('Курс: 1 ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(exch_rate) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                change_list.append('Сумма сделки: ' + str(full_request.SendAmount) + ' ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(full_request.ReceiveAmount) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                # change_list.append('Комиссия платформы: ' + str(old_reserve) + 'USDT' + ' -> ' + str(new_reserve)  + 'USDT')
                            else:
                                change_list.append('Клиент указал фиксированное кол-во актива к покупке')
                                change_list.append('Курс: 1 ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(exch_rate) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                change_list.append('Сумма сделки: ' + str(full_request.SendAmount) + ' ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(full_request.ReceiveAmount) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                # change_list.append('Комиссия платформы: ' + str(old_reserve) + 'USDT' + ' -> ' + str(new_reserve) + 'USDT')
                        order.SendAmount = None
                elif form.cleaned_data.get('Send_or_Receive') == 'Кол-во контрактива к продаже':
                    if order.SendAmount != form.cleaned_data.get("Order_amount") or param_exchange==1 or param_pricetype==1 or param_finoffice!=0:
                        order.SendAmount = form.cleaned_data.get("Order_amount")
                        Requests_data = Requests.objects.filter(OrderID=order.pk).values('pk', 'PCCNTR', 'ExchangePointID')
                        if len(Requests_data) != 0:
                            for request_data in Requests_data:
                                full_request = Requests.objects.get(OrderID=order.pk, PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID'])
                                opertype = ExchangeID.objects.filter(pk=order.ExchangeID).values_list('OperTypes', flat=True)[0]
                                OPRTs = []
                                if ';' in opertype:
                                    while ';' in opertype:
                                        oprt = opertype[:opertype.find(";")].strip()
                                        OPRTs.append(oprt)
                                        opertype = opertype[opertype.find(";") + 1:].strip()
                                    OPRTs.append(opertype.strip())
                                else:
                                    OPRTs.append(opertype.strip())
                                if len(OPRTs) == 1:
                                    currency_value = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                          FinOfficeFrom=order.FinOfficeFrom,
                                                                                          FinOfficeTo=order.FinOfficeTo,
                                                                                          QuotesRC=
                                                                                          PCCNTR_OperTypes.objects.filter(
                                                                                              PCCNTR=request_data['PCCNTR'],
                                                                                              OperType=OPRTs[
                                                                                                  0]).values_list(
                                                                                              'QuotesRC',
                                                                                              flat=True)[
                                                                                              0]).values_list(
                                        'Value', flat=True)[0])
                                    currency_full_value = round(float(order.SendAmount) * currency_value, 2)
                                    exchange_rate = currency_value
                                elif len(OPRTs) == 2:
                                    currency_value_1 = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                            FinOfficeFrom=order.FinOfficeFrom,
                                                                                            FinOfficeTo='TRC20',
                                                                                            QuotesRC=
                                                                                            PCCNTR_OperTypes.objects.filter(
                                                                                                PCCNTR=request_data['PCCNTR'],
                                                                                                OperType=OPRTs[0]).values_list(
                                                                                                'QuotesRC',
                                                                                                flat=True)[
                                                                                                0]).values_list(
                                        'Value', flat=True)[
                                                                 0])
                                    currency_value_2 = float(Currency_source.objects.filter(OperType=OPRTs[1],
                                                                                            FinOfficeFrom='TRC20',
                                                                                            FinOfficeTo=order.FinOfficeTo,
                                                                                            QuotesRC=
                                                                                            PCCNTR_OperTypes.objects.filter(
                                                                                                PCCNTR=request_data['PCCNTR'],
                                                                                                OperType=OPRTs[
                                                                                                    0]).values_list(
                                                                                                'QuotesRC',
                                                                                                flat=True)[
                                                                                                0]).values_list(
                                        'Value', flat=True)[
                                                                 0])
                                    exchange_rate = round(currency_value_1 * currency_value_2, 5)
                                    currency_full_value = round(float(order.SendAmount) * exchange_rate, 2)
                                # Добавить проверку на минимальный и максимальный размер обмена - если вне рамок, то деактивируем предложение
                                profit_norm = EP_ExchangeID.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                        ExchangePointID=request_data['ExchangePointID'],
                                                                        ExchangeTransferID=order.ExchangeID)
                                # print(exchange_rate)
                                # print(currency_full_value)
                                # print(profit_norm.ExchTOAmount_Min)
                                # print(profit_norm.ExchTOAmount_Max)
                                if currency_full_value < profit_norm.ExchTOAmount_Min and currency_full_value > profit_norm.ExchTOAmount_Max:
                                    Requests.objects.filter(OrderID=order.pk, PCCNTR=request_data['PCCNTR'],ExchangePointID=request_data['ExchangePointID']).delete()
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                               OrderID=order.pk,
                                                               RequestID=request_data['pk']).delete()
                                    PCCNTR_data.save()

                                    partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType='PART')
                                    Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                                                 PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                                 Text='Предложение по заявке на обмен №' + str(
                                                                     order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                    mail_subject = 'Изменения в заявке на обмен'
                                    email = \
                                        User.objects.filter(username=partner_contacts.TG_Contact).values_list('email',
                                                                                                              flat=True)[0]
                                    to_email = email
                                    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                    html_content = get_template(
                                        'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                        'user': partner_contacts.TG_Contact,
                                        'OrderNum': order.pk,
                                    })
                                    msg.attach_alternative(html_content, "text/html")
                                    res = msg.send()

                                    org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                            ContactType='ORG',
                                                                            ExchangePointID__contains=request_data[
                                                                                'ExchangePointID'])
                                    if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                                        Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                                     PCCNTR=request_data['PCCNTR'],
                                                                     ExchangePointID=request_data['ExchangePointID'],
                                                                     Text='Предложение по заявке на обмен №' + str(
                                                                         order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                        mail_subject = 'Изменения в заявке на обмен'
                                        email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email',
                                                                                                                  flat=True)[
                                            0]
                                        to_email = email
                                        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                        html_content = get_template(
                                            'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                            'user': org_contacts.TG_Contact,
                                            'OrderNum': order.pk,
                                        })
                                        msg.attach_alternative(html_content, "text/html")
                                        res = msg.send()

                                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                                    empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType__in=job_positions,
                                                                                ExchangePointID__contains=request_data[
                                                                                    'ExchangePointID']).values('TG_Contact',
                                                                                                               'ContactType')
                                    for empl in empl_contacts:
                                        if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                                            'TG_Contact'] != org_contacts.TG_Contact:
                                            Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                                                         ContactType=empl['ContactType'],
                                                                         PCCNTR=request_data['PCCNTR'],
                                                                         ExchangePointID=request_data['ExchangePointID'],
                                                                         Text='Предложение по заявке на обмен №' + str(
                                                                             order.pk) + ' была отменена по причине смены cуммы сделки, <br> которая выходит за рамки, указанные в настройках обменника')
                                            mail_subject = 'Изменения в заявке на обмен'
                                            email = User.objects.filter(username=empl['TG_Contact']).values_list('email',
                                                                                                                 flat=True)[
                                                0]
                                            to_email = email
                                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                            html_content = get_template(
                                                'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                                'user': empl['TG_Contact'],
                                                'OrderNum': order.pk,
                                            })
                                            msg.attach_alternative(html_content, "text/html")
                                            res = msg.send()


                                    continue
                                elif order.PriceType == 'Плавающая' or param_exchange==1 or param_pricetype==1 or param_finoffice!=0:
                                    Norm_Prib = profit_norm.EP_PRFTNORM
                                    Norm_Prib_Name_1 = []
                                    Norm_Prib_Name_2 = []
                                    Norm_Prib_Percent = []
                                    if ';' in Norm_Prib:
                                        while ";" in Norm_Prib:
                                            N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
                                            Name = N_P[:N_P.find(' ')].strip()
                                            Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
                                            Name_1 = Name[:Name.find("-")].strip()
                                            Norm_Prib_Name_1.append(Name_1)
                                            Name_2 = Name[Name.find("-") + 1:].strip()
                                            Norm_Prib_Name_2.append(Name_2)
                                            Norm_Prib_Percent.append(Percent)
                                            Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
                                        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                                        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                                        Name_1 = Name[:Name.find("-")].strip()
                                        Norm_Prib_Name_1.append(Name_1)
                                        Name_2 = Name[Name.find("-") + 1:].strip()
                                        Norm_Prib_Name_2.append(Name_2)
                                        Norm_Prib_Percent.append(Percent)
                                    else:
                                        Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                                        Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                                        Name_1 = Name[:Name.find("-")].strip()
                                        Norm_Prib_Name_1.append(Name_1)
                                        Name_2 = Name[Name.find("-") + 1:].strip()
                                        Norm_Prib_Name_2.append(Name_2)
                                        Norm_Prib_Percent.append(Percent)

                                    for i in range(len(Norm_Prib_Name_1)):
                                        if currency_full_value >= float(Norm_Prib_Name_1[i]) and currency_full_value <= float(Norm_Prib_Name_2[i]):
                                            max_percent_new = float(Norm_Prib_Percent[i])

                                    exch_rate = round(exchange_rate * (1 - max_percent_new / 100),5)
                                    # print(exch_rate)
                                    full_request.SendAmount = order.SendAmount
                                    full_request.ReceiveAmount = round(order.SendAmount * exch_rate,2)
                                else:
                                    # Дописать перерасчет получаемой суммы зная курс в таблице Requests
                                    exch_rate = round(full_request.ReceiveAmount / full_request.SendAmount,5)
                                    # print(exch_rate)
                                    full_request.SendAmount = order.SendAmount
                                    full_request.ReceiveAmount = round(order.SendAmount * exch_rate,2)

                                # Cчитаем отдаваемую и получаемую сумму в USDT (дописать поиск получаемой суммы)
                                if form.cleaned_data.get("Currency_to_sell") != 'USDT' and form.cleaned_data.get("Currency_to_buy") != 'USDT':
                                    sumusdt_send = int(order.SendAmount * float(
                                        Currency_source.objects.get(OperType=str(form.cleaned_data.get("Currency_to_sell")) + " => USDT",
                                                                    FinOfficeFrom='Наличные',
                                                                    FinOfficeTo='TRC20',
                                                                    QuotesRC='GARALL').Value))
                                    sumusdt_receive = int(full_request.ReceiveAmount * float(
                                        Currency_source.objects.get(OperType=str(form.cleaned_data.get("Currency_to_buy")) + " => USDT",
                                                                    FinOfficeFrom='Наличные',
                                                                    FinOfficeTo='TRC20',
                                                                    QuotesRC='GARALL').Value))
                                elif form.cleaned_data.get("Currency_to_sell") == 'USDT':
                                    sumusdt_send = int(order.SendAmount)
                                    sumusdt_receive = int(order.SendAmount)
                                else:
                                    sumusdt_send = int(full_request.ReceiveAmount)
                                    sumusdt_receive = int(full_request.ReceiveAmount)

                                # Cчитаем отдаваемую и получаемую сумму в EUR (дописать поиск получаемой суммы)
                                if form.cleaned_data.get("Currency_to_sell") != 'EUR' and form.cleaned_data.get("Currency_to_buy") != 'EUR':
                                    sumeur_send = int(sumusdt_send * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                                       FinOfficeFrom='TRC20',
                                                                                                       FinOfficeTo='Наличные',
                                                                                                       QuotesRC='GARALL').Value))
                                    sumeur_receive = int(
                                        sumusdt_receive * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                            FinOfficeFrom='TRC20',
                                                                                            FinOfficeTo='Наличные',
                                                                                            QuotesRC='GARALL').Value))
                                elif form.cleaned_data.get("Currency_to_sell") == 'EUR':
                                    sumeur_send = int(order.SendAmount)
                                    sumeur_receive = int(order.SendAmount)
                                else:
                                    sumeur_send = int(full_request.ReceiveAmount)
                                    sumeur_receive = int(full_request.ReceiveAmount)

                                balance_amount = float(PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR']).Balance) - float(PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR']).Reserve) + float(DealReserve.objects.get(PCCNTR=request_data['PCCNTR'], OrderID=order.pk, RequestID=request_data['pk']).Reserve_Amount)
                                # print(balance_amount)

                                # Проверка на баланс обменника (хватает ли денег на комиссию в случае изменения стоимости обмена)
                                if int(sumusdt_receive * 0.01) > balance_amount:
                                    Requests.objects.filter(OrderID=order.pk, PCCNTR=request_data['PCCNTR'],ExchangePointID=request_data['ExchangePointID']).delete()
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                               OrderID=order.pk,
                                                               RequestID=request_data['pk']).delete()
                                    PCCNTR_data.save()

                                    partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType='PART')
                                    Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                                                 PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                                 Text='Предложение по заявке на обмен №' + str(
                                                                     order.pk) + ' было отменено по причине недостатка средств для оплаты комиссии платформы')
                                    mail_subject = 'Изменения в заявке на обмен'
                                    email = \
                                        User.objects.filter(username=partner_contacts.TG_Contact).values_list('email',
                                                                                                              flat=True)[0]
                                    to_email = email
                                    msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                    html_content = get_template(
                                        'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                        'user': partner_contacts.TG_Contact,
                                        'OrderNum': order.pk,
                                    })
                                    msg.attach_alternative(html_content, "text/html")
                                    res = msg.send()

                                    org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                            ContactType='ORG',
                                                                            ExchangePointID__contains=request_data[
                                                                                'ExchangePointID'])
                                    if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                                        Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                                     PCCNTR=request_data['PCCNTR'],
                                                                     ExchangePointID=request_data['ExchangePointID'],
                                                                     Text='Предложение по заявке на обмен №' + str(
                                                                         order.pk) + ' было отменено по причине недостатка средств для оплаты комиссии платформы')
                                        mail_subject = 'Изменения в заявке на обмен'
                                        email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email',
                                                                                                                  flat=True)[
                                            0]
                                        to_email = email
                                        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                        html_content = get_template(
                                            'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                            'user': org_contacts.TG_Contact,
                                            'OrderNum': order.pk,
                                        })
                                        msg.attach_alternative(html_content, "text/html")
                                        res = msg.send()

                                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                                    empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'],
                                                                                ContactType__in=job_positions,
                                                                                ExchangePointID__contains=request_data[
                                                                                    'ExchangePointID']).values('TG_Contact',
                                                                                                               'ContactType')
                                    for empl in empl_contacts:
                                        if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                                            'TG_Contact'] != org_contacts.TG_Contact:
                                            Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                                                         ContactType=empl['ContactType'],
                                                                         PCCNTR=request_data['PCCNTR'],
                                                                         ExchangePointID=request_data['ExchangePointID'],
                                                                         Text='Предложение по заявке на обмен №' + str(
                                                                             order.pk) + ' было отменено по причине недостатка средств для оплаты комиссии платформы')
                                            mail_subject = 'Изменения в заявке на обмен'
                                            email = User.objects.filter(username=empl['TG_Contact']).values_list('email',
                                                                                                                 flat=True)[
                                                0]
                                            to_email = email
                                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                            html_content = get_template(
                                                'testsite/send_notification_to_PCCNTR_change_order_delete.html').render({
                                                'user': empl['TG_Contact'],
                                                'OrderNum': order.pk,
                                            })
                                            msg.attach_alternative(html_content, "text/html")
                                            res = msg.send()

                                    continue
                                else:
                                    DealReserve_data = DealReserve.objects.get(PCCNTR=request_data['PCCNTR'],
                                                                               OrderID=order.pk,
                                                                               RequestID=request_data['pk'])
                                    PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=request_data['PCCNTR'])
                                    # old_reserve = DealReserve_data.Reserve_Amount
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
                                    DealReserve_data.Reserve_Amount = int(sumusdt_receive * 0.01)
                                    # new_reserve = int(sumusdt_receive * 0.01)
                                    PCCNTR_data.Reserve = PCCNTR_data.Reserve + DealReserve_data.Reserve_Amount
                                    DealReserve_data.save()
                                    PCCNTR_data.save()

                                full_request.ExchRateEURUSDT = round(sumusdt_receive / sumeur_send, 5)
                                full_request.ExchRateUSDTEUR = round(sumeur_receive / sumusdt_send, 5)
                                full_request.sendinEUR = sumeur_send
                                full_request.receiveinEUR = sumeur_receive
                                full_request.sendinUSDT = sumusdt_send
                                full_request.receiveinUSDT = sumusdt_receive

                                full_request.save()

                            if order.ReceiveAmount is None:
                                change_list.append('Курс: 1 ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(exch_rate) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                change_list.append('Сумма сделки: ' + str(order.SendAmount) + ' ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(full_request.ReceiveAmount) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                # change_list.append('Комиссия платформы: ' + str(old_reserve) + 'USDT' + ' -> ' + str(new_reserve)  + 'USDT')
                            else:
                                change_list.append('Клиент указал фиксированное кол-во контрактива к продаже')
                                change_list.append('Курс: 1 ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(exch_rate) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                change_list.append('Сумма сделки: ' + str(order.SendAmount) + ' ' + form.cleaned_data.get("Currency_to_sell") + ' = ' + str(full_request.ReceiveAmount) + ' ' + form.cleaned_data.get("Currency_to_buy"))
                                # change_list.append('Комиссия платформы: ' + str(old_reserve) + 'USDT' + ' -> ' + str(new_reserve) + 'USDT')
                        order.ReceiveAmount = None



                if order.TimeInterval != form.cleaned_data.get("Order_time"):
                    change_list.append('Время сделки: ' + str(order.TimeInterval) + ' -> ' + str(form.cleaned_data.get("Order_time")))
                    order.TimeInterval = form.cleaned_data.get("Order_time")

                city = Cities.objects.filter(Name_RUS=form.cleaned_data.get("CITY")).values('City_code', 'Country')

                if order.City != city[0]['City_code']:
                    change_list.append('Место сделки: ' + str(Cities.objects.filter(City_code=order.City).values('Name_RUS')[0]['Name_RUS']) + ' -> ' + str(form.cleaned_data.get("CITY")))
                    order.City = city[0]['City_code']

                if order.DeliveryType != '; '.join(form.cleaned_data.get("DeliveryType")):
                    change_list.append('Способ доставки: ' + str(order.DeliveryType) + ' -> ' + str('; '.join(form.cleaned_data.get("DeliveryType"))))
                    order.DeliveryType = '; '.join(form.cleaned_data.get("DeliveryType"))

                if order.OrderLimit != form.cleaned_data.get("Limit_amount"):
                    change_list.append('Лимит сделки: ' + str(order.OrderLimit) + ' -> ' + str(form.cleaned_data.get("Limit_amount")))
                    order.OrderLimit = form.cleaned_data.get("Limit_amount")

                if order.Comment != form.cleaned_data.get("Comment"):
                    change_list.append('Комментарий: ' + str(order.Comment) + ' -> ' + str(form.cleaned_data.get("Comment")))
                    order.Comment = form.cleaned_data.get("Comment")

                order.save()

                if len(change_list) != 0:
                    all_changes = '<br>'.join(change_list)

                    Requests_data = Requests.objects.filter(OrderID=order.pk).values('pk', 'PCCNTR', 'ExchangePointID')
                    for request_data in Requests_data:
                        full_request = Requests.objects.get(OrderID=order.pk, PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID'])
                        full_request.Active = False
                        full_request.save()
                        button_confirm_decline = '<br> <div style="text-align:center; "><button style="background-color: lawngreen; font-size: 12px">  <a href="confirm_order_changes/' + str(request_data['pk']) +  '/">Принять изменения</a> </button> <button style="background-color: orangered; font-size: 12px"><a href="decline_order_changes/' + str(request_data['pk']) +  '/">Отклонить изменения и удалить предложение</a> </button></div>'
                        partner_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'], ContactType='PART')
                        Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART', PCCNTR=request_data['PCCNTR'], ExchangePointID='-',
                                                 Text='Клиент ' + str(order.TG_Contact) + ' внес изменения в заявку на обмен №'
                                                      + str(order.pk) + ':<br> ' + str(all_changes) + button_confirm_decline)

                        mail_subject = 'Изменения в заявке на обмен'
                        email = User.objects.filter(username=partner_contacts.TG_Contact).values_list('email', flat=True)[0]
                        to_email = email
                        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                        html_content = get_template('testsite/send_notification_to_PCCNTR_change_order.html').render({
                            'user': partner_contacts.TG_Contact,
                            'Client': order.TG_Contact,
                            'OrderNum': order.pk,
                        })
                        msg.attach_alternative(html_content, "text/html")
                        res = msg.send()

                        org_contacts = Users_PCCNTR.objects.get(PCCNTR=request_data['PCCNTR'], ContactType='ORG', ExchangePointID__contains=request_data['ExchangePointID'])
                        if org_contacts.TG_Contact != partner_contacts.TG_Contact:
                            Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                                         PCCNTR=request_data['PCCNTR'], ExchangePointID=request_data['ExchangePointID'],
                                                         Text='Клиент ' + str(
                                                             order.TG_Contact) + ' внес изменения в заявку на обмен №'
                                                              + str(order.pk) + ':<br> ' + str(all_changes) + button_confirm_decline)
                            mail_subject = 'Изменения в заявке на обмен'
                            email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email', flat=True)[0]
                            to_email = email
                            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                            html_content = get_template('testsite/send_notification_to_PCCNTR_change_order.html').render({
                                'user': org_contacts.TG_Contact,
                                'Client': order.TG_Contact,
                                'OrderNum': order.pk,
                            })
                            msg.attach_alternative(html_content, "text/html")
                            res = msg.send()

                        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                        empl_contacts = Users_PCCNTR.objects.filter(PCCNTR=request_data['PCCNTR'], ContactType__in=job_positions, ExchangePointID__contains=request_data['ExchangePointID']).values('TG_Contact', 'ContactType')
                        for empl in empl_contacts:
                            if empl['TG_Contact'] != partner_contacts.TG_Contact and empl['TG_Contact'] != org_contacts.TG_Contact:
                                Notifications.objects.create(TG_Contact=empl['TG_Contact'], ContactType=empl['ContactType'],
                                                             PCCNTR=request_data['PCCNTR'],
                                                             ExchangePointID=request_data['ExchangePointID'],
                                                             Text='Клиент ' + str(
                                                                 order.TG_Contact) + ' внес изменения в заявку на обмен №'
                                                                  + str(order.pk) + ':<br> ' + str(all_changes) + button_confirm_decline)
                                mail_subject = 'Изменения в заявке на обмен'
                                email = User.objects.filter(username=empl['TG_Contact']).values_list('email', flat=True)[0]
                                to_email = email
                                msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                                html_content = get_template('testsite/send_notification_to_PCCNTR_change_order.html').render({
                                    'user': empl['TG_Contact'],
                                    'Client': order.TG_Contact,
                                    'OrderNum': order.pk,
                                })
                                msg.attach_alternative(html_content, "text/html")
                                res = msg.send()

                return redirect('P2Pmarket_Bulletin_board')
    else:
        order = Orders.objects.get(pk=num)
        Date = order.OrderDate
        if order.SendAmount is None:
            s_r = 'Кол-во актива к покупке'
            Amount = order.ReceiveAmount
        elif order.ReceiveAmount is None:
            s_r = 'Кол-во контрактива к продаже'
            Amount = order.SendAmount

        if order.ReceiveTransferType == "CSH":
            p_t_b = "Наличные"
        elif order.ReceiveTransferType == "CRP":
            p_t_b = "Перевод по сети блокчейн"
        elif order.ReceiveTransferType == "CRD":
            p_t_b = "Карточный перевод"

        if order.SendTransferType == "CSH":
            p_t_s = "Наличные"
        elif order.SendTransferType == "CRP":
            p_t_s = "Перевод по сети блокчейн"
        elif order.SendTransferType == "CRD":
            p_t_s = "Карточный перевод"

        del_type = []
        if ';' in order.DeliveryType:
            del_type = ['Курьер', 'Офис']
        else:
            del_type.append(order.DeliveryType)

        form = Changeexchangeorder(request.user, {
            'Currency_to_sell': order.SendCurrencyISO
            , 'Currency_to_buy': order.ReceiveCurrencyISO
            , 'PriceType': order.PriceType
            , 'Pay_type_sell': p_t_s
            , 'FinOfficeFrom': order.FinOfficeFrom
            , 'Pay_type_buy': p_t_b
            , 'FinOfficeTo': order.FinOfficeTo
            , 'CITY': Cities.objects.filter(City_code=order.City).values('Name_RUS')[0]['Name_RUS']
            , 'Order_time': order.TimeInterval
            , 'DeliveryType': del_type
            , 'Send_or_Receive': s_r
            , 'Order_amount': Amount
            , 'Limit_amount': order.OrderLimit
            , 'Comment': order.Comment
        })
        return render(request, 'testsite/P2Pmarket_Exchange_order.html',
                      {'title': 'Редактирование заявки на обмен', 'form': form, 'param': 1, 'error': "",
                       'Country': Country, 'Date': Date, 'balance': user.balanceFull, 'num': num})

#
def P2Pmarket_Bulletin_board(request): # добавить фильтр на дату и время сделки
    # global user_type, ExchangeName, orders_for_board
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user
    user = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
    orders_for_board = {}
    status = ['Создан']
    if user_type == 'Клиент':
        #print(1)
        Order_for_board = (Orders.objects.filter(TG_Contact=username, Status__in=status)
                                    .values("pk", "ExchangeID","SendAmount","ReceiveAmount",
                                           "FinOfficeFrom","FinOfficeTo","OrderDate",
                                           "TimeInterval","Country", "City",
                                           "DeliveryType","Comment", 'OrderLimit',
                                           'PriceType', 'Status').order_by("-CreatedDate"))
        # orders_with_requests = []

    elif user_type == 'Партнер':
        #print(2)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR', 'ContactType',
                                                                             'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат

        cities = []
        ExchangePointCities = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangePointCity',
                                                                                              flat=True).order_by(
            'ExchangePointName')
        EPID = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangePointID', flat=True)

        for city in list(ExchangePointCities):
            if ";" in city:
                while ";" in city:
                    c = city[:city.find(";")]
                    cities.append(c)
                    city = city[city.find(";") + 1:]
                cities.append(city[1:])
            else:
                cities.append(city)

        #
        # opertype_names = PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('OperType', flat=True)
        # print(opertype_names)
        exchange_ids = list(ExchangeID.objects.filter(pk__in = list(EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code).values_list('ExchangeTransferID', flat=True))).values_list('pk',flat=True).distinct())
        # print(exchange_ids)
        Order_for_board = Orders.objects.filter(City__in=cities, Status__in=status, ExchangeID__in=exchange_ids).values(
            "pk", "ExchangeID", "SendAmount", "SendTransferType",'ReceiveTransferType',
            "ReceiveAmount", "FinOfficeFrom", "FinOfficeTo", "OrderDate", "TimeInterval",
            "Country", "City", "DeliveryType", "Comment", 'OrderLimit', 'PriceType', 'Status').order_by("-CreatedDate")
        # print(Order_for_board)
        # Order_for_board_ids = Orders.objects.filter(City__in=cities, Status='Создан',
        #                                             ExchangeID__in=opertype_ids).values_list("pk", flat=True).order_by(
        #     "-CreatedDate")

    elif user_type == 'Организатор':
        #print(3)
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                       flat=True).order_by(
            'ExchangePointID')
        # EPID_str = '; '.join(EPID)
        # user = pcc = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType='ORG',
        #                                          ExchangePointID=EPID_str).values('TG_Contact', 'PCCNTR', 'ContactType',
        #                                                                           'ExchangePointID')
        pcc_code = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values('PCCNTR')[0]['PCCNTR']
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc_code)
        cities = []
        ExchangePoint = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointCity',
                                                                                                flat=True).order_by(
            'ExchangePointName')

        for city in list(ExchangePoint):
            if ";" in city:
                while ";" in city:
                    c = city[:city.find(";")]
                    cities.append(c)
                    city = city[city.find(";") + 1:]
                cities.append(city[1:])
            else:
                cities.append(city)

        exchange_ids = list(ExchangeID.objects.filter(pk__in=list(
            EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID__in=EPID).values_list('ExchangeTransferID',flat=True))).values_list('pk',flat=True).distinct())
        Order_for_board = Orders.objects.filter(City__in=cities, Status__in=status, ExchangeID__in=exchange_ids).values(
            "pk", "ExchangeID", "SendAmount",
            "ReceiveAmount", "FinOfficeFrom", 'FinOfficeTo',
            "OrderDate", "TimeInterval",
            "Country",
            "City", "DeliveryType",
            "Comment", 'OrderLimit', 'PriceType', "Status").order_by("-CreatedDate")

    else:
        #print(4)
        ExchangeName = urllib.parse.unquote(ExchangeName)
        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID', flat=True)
        user_pccntr = Users_PCCNTR.objects.get(TG_Contact=username, ContactType__in=job_positions,
                                               ExchangePointID__in=EPID)
        cities = []
        city = user_pccntr.CITY
        if ";" in city:
            while ";" in city:
                c = city[:city.find(";")]
                cities.append(c)
                city = city[city.find(";") + 1:]
            cities.append(city[1:])
        else:
            cities.append(city )
        pcc_name = PCCNTR.objects.get(PCCNTR_code=user_pccntr.PCCNTR)
        exchange_ids = list(ExchangeID.objects.filter(pk__in=list(
                                            EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                            ExchangePointID=user_pccntr.ExchangePointID).values_list(
                                            'ExchangeTransferID', flat=True))).values_list('pk', flat=True).distinct())
        if ';' in user_pccntr.ContactType:
            Order_for_board = Orders.objects.filter(City__in=cities, Status__in=status,
                                                    ExchangeID__in=exchange_ids).values("pk", "ExchangeID",
                                                                                        "SendAmount",
                                                                                        "ReceiveAmount",
                                                                                        "FinOfficeFrom", "FinOfficeTo",
                                                                                        "OrderDate",
                                                                                        "TimeInterval", "Country",
                                                                                        "City", "DeliveryType",
                                                                                        "Comment", 'OrderLimit',
                                                                                        'PriceType', 'Status').order_by(
                "-CreatedDate")

        else:
            if user_pccntr.ContactType == 'CUR':
                DeliveryTypes = ['Курьер; Офис', 'Офис; Курьер', 'Офис']
            elif user_pccntr.ContactType == 'COUR':
                DeliveryTypes = ['Курьер; Офис', 'Офис; Курьер', 'Курьер']

            Order_for_board = Orders.objects.filter(City__in=user_pccntr.CITY, DeliveryType__in=DeliveryTypes,
                                                    Status__in=status, ExchangeID__in=exchange_ids).values("pk",
                                                                                                         "ExchangeID",
                                                                                                         "SendAmount",
                                                                                                         "ReceiveAmount",
                                                                                                         "FinOfficeFrom",
                                                                                                         "FinOfficeTo",
                                                                                                         "OrderDate",
                                                                                                         "TimeInterval",
                                                                                                         "Country",
                                                                                                         "City",
                                                                                                         "DeliveryType",
                                                                                                         "Comment",
                                                                                                         'OrderLimit',
                                                                                                         'PriceType',
                                                                                                         'Status').order_by(
                "-CreatedDate")

    # print(Order_for_board[0])
    # print(Order_for_board)
    for order in Order_for_board:
        # print(order)
        request_param = 0
        ExchangeType = ExchangeID.objects.filter(pk=order['ExchangeID']).values('pk',"Name_RUS", "SendCurrencyISO",
                                                                                    "ReceiveCurrencyISO",
                                                                                    "SendTransferType",
                                                                                    'ReceiveTransferType')
        if ExchangeType[0]['SendTransferType'] == "CRP":
            SendTransferType = "Перевод по сети блокчейн"
        elif ExchangeType[0]['SendTransferType'] == "CRD":
            SendTransferType = "Карточный перевод"
        elif ExchangeType[0]['SendTransferType'] == "CSH":
            SendTransferType = "Наличные"

        if ExchangeType[0]['ReceiveTransferType'] == "CRP":
            ReceiveTransferType = "Перевод по сети блокчейн"
        elif ExchangeType[0]['ReceiveTransferType'] == "CRD":
            ReceiveTransferType = "Карточный перевод"
        elif ExchangeType[0]['ReceiveTransferType'] == "CSH":
            ReceiveTransferType = "Наличные"


        city = Cities.objects.filter(City_code=order['City']).values('Name_RUS')[0]['Name_RUS']
        country = Countries.objects.filter(Country_code=order['Country']).values('Name_RUS')[0]['Name_RUS']
        if user_type == 'Клиент':
            orders_for_board[order['pk']] = {'num': order['pk'], "ExchangeType": ExchangeType[0]['Name_RUS'],
                                             "SendAmount": str(order['SendAmount']) + " " + str(
                                                 ExchangeType[0]['SendCurrencyISO']),
                                             "ReceiveAmount": str(order['ReceiveAmount']) + " " + str(
                                                 ExchangeType[0]['ReceiveCurrencyISO']),
                                             "SendTransferType": SendTransferType,
                                             "ReceiveTransferType": ReceiveTransferType,
                                             "FinOfficeFrom": order['FinOfficeFrom'],
                                             "FinOfficeTo": order['FinOfficeTo'],
                                             "OrderDate": order['OrderDate'],
                                             "TimeInterval": order["TimeInterval"],
                                             "Country": country,
                                             "City": city,
                                             "DeliveryType": order['DeliveryType'],
                                             "Comment": order['Comment'],
                                             'OrderLimit': order['OrderLimit'],
                                             'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                             'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                             'Status': order['Status'],
                                             'request_param': 0
                                             }
            if order['Status'] == 'Создан':
                requests_for_order = len(Requests.objects.filter(OrderID=order['pk']).values_list('pk', flat=True))
                if requests_for_order != 0:
                    orders_for_board[order['pk']]['request_param'] = 1

        elif user_type == 'Организатор' or user_type == 'Партнер':
            if user_type == 'Организатор':
                Min_Max_PrftNorms = (EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                                 ExchangeTransferID=ExchangeType[0]['pk'],
                                                                 ExchangePointID__in=EPID).values('ExchTOAmount_Min',
                                                                                                  'ExchTOAmount_Max',
                                                                                                  'EP_PRFTNORM').distinct())
            else:
                Min_Max_PrftNorms = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                                 ExchangeTransferID=ExchangeType[0]['pk']).values('ExchTOAmount_Min', 'ExchTOAmount_Max', 'EP_PRFTNORM').distinct()
            # print(Min_Max_PrftNorms)
            for Min_Max_PrftNorm in Min_Max_PrftNorms:
                # prft_norm = [Min_Max_PrftNorm]
                # print(Min_Max_PrftNorm)
                if order['ReceiveAmount'] is not None and order['ReceiveAmount'] >= Min_Max_PrftNorm['ExchTOAmount_Min'] and order['ReceiveAmount'] <= Min_Max_PrftNorm['ExchTOAmount_Max'] and order['pk'] not in list(orders_for_board.keys()):
                    # print(1)
                    EPID_2 = (EP_ExchangeID.objects.filter(ExchTOAmount_Min=Min_Max_PrftNorm['ExchTOAmount_Min'],
                                                          ExchTOAmount_Max=Min_Max_PrftNorm['ExchTOAmount_Max'],
                                                          EP_PRFTNORM=Min_Max_PrftNorm['EP_PRFTNORM'])
                                                                                .values_list('ExchangePointID', flat=True))
                    Countries_list = Countries.objects.filter(
                        Country_code__in=PCCNTR_ExchP.objects.filter(ExchangePointID__in=EPID_2).values_list(
                            'ExchangePointCountry', flat=True).distinct()).values_list('Name_RUS', flat=True).distinct()
                    if country in Countries_list:
                        orders_with_requests_ep = Requests.objects.filter(OrderID=order['pk']).values_list(
                            'ExchangePointID', flat=True)
                        for exchp in EPID:
                            if exchp in orders_with_requests_ep:
                                request_param += 1

                        orders_for_board[order['pk']] = {'num': order['pk'],
                                                         "ExchangeType": ExchangeType[0]['Name_RUS'],
                                                         "SendAmount": str(order['SendAmount']) + " " + str(
                                                             ExchangeType[0]['SendCurrencyISO']),
                                                         "ReceiveAmount": str(order['ReceiveAmount']) + " " + str(
                                                             ExchangeType[0]['ReceiveCurrencyISO']),
                                                         "SendTransferType": SendTransferType,
                                                         "ReceiveTransferType": ReceiveTransferType,
                                                         "FinOfficeFrom": order['FinOfficeFrom'],
                                                         "FinOfficeTo": order['FinOfficeTo'],
                                                         "OrderDate": order['OrderDate'],
                                                         "TimeInterval": order["TimeInterval"],
                                                         "Country": country,
                                                         "City": city,
                                                         "DeliveryType": order['DeliveryType'],
                                                         "Comment": order['Comment'],
                                                         'OrderLimit': order['OrderLimit'],
                                                         'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                                         'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                                         'Status': order['Status'],
                                                         'request_param': request_param
                                                         }

                        break


                elif order['SendAmount'] is not None:
                    # print(2)
                    opertype = ExchangeID.objects.filter(pk=order['ExchangeID']).values_list('OperTypes', flat=True)[0]
                    # print(opertype)
                    OPRTs = []
                    if ';' in opertype:
                        while ';' in opertype:
                            oprt = opertype[:opertype.find(";")].strip()
                            OPRTs.append(oprt)
                            opertype = opertype[opertype.find(";") + 1:].strip()
                        OPRTs.append(opertype.strip())
                    else:
                        OPRTs.append(opertype.strip())
                    # print(OPRTs)
                    if len(OPRTs) == 1:
                        currency_value = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                        FinOfficeFrom=order['FinOfficeFrom'],
                                                                        FinOfficeTo=order['FinOfficeTo'],
                                                                        QuotesRC=PCCNTR_OperTypes.objects.filter(PCCNTR=pcc_name.PCCNTR_code, OperType=OPRTs[0]).values_list('QuotesRC',flat=True)[0]).values_list('Value', flat=True)[0])
                        ReceiveAmount = round(float(order['SendAmount']) * currency_value,2)
                        # print(float(order['SendAmount']))
                        # print(currency_value)
                        # print(ReceiveAmount)

                    elif len(OPRTs) == 2:
                        currency_value_1 = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                              FinOfficeFrom=order['FinOfficeFrom'],
                                                                              FinOfficeTo='TRC20',
                                                                              QuotesRC=PCCNTR_OperTypes.objects.filter(
                                                                                  PCCNTR=pcc_name.PCCNTR_code,
                                                                                  OperType=OPRTs[0]).values_list(
                                                                                  'QuotesRC', flat=True)[
                                                                                  0]).values_list('Value', flat=True)[
                                                   0])
                        currency_value_2 = float(Currency_source.objects.filter(OperType=OPRTs[1],
                                                                                FinOfficeFrom='TRC20',
                                                                                FinOfficeTo=order['FinOfficeTo'],
                                                                                QuotesRC=
                                                                                PCCNTR_OperTypes.objects.filter(
                                                                                    PCCNTR=pcc_name.PCCNTR_code,
                                                                                    OperType=OPRTs[1]).values_list(
                                                                                    'QuotesRC', flat=True)[
                                                                                    0]).values_list('Value', flat=True)[
                                                     0])
                        ReceiveAmount = round(float(order['SendAmount']) * currency_value_1 * currency_value_2, 2)
                        # print(float(order['SendAmount']))
                        # print(currency_value_1)
                        # print(currency_value_2)
                        # print(ReceiveAmount)
                    if ReceiveAmount >= Min_Max_PrftNorm['ExchTOAmount_Min'] and ReceiveAmount <= Min_Max_PrftNorm['ExchTOAmount_Max'] and order['pk'] not in list(orders_for_board.keys()):
                        EPID_2 = EP_ExchangeID.objects.filter(ExchTOAmount_Min=Min_Max_PrftNorm['ExchTOAmount_Min'],
                                                              ExchTOAmount_Max=Min_Max_PrftNorm['ExchTOAmount_Max'],
                                                              EP_PRFTNORM=Min_Max_PrftNorm['EP_PRFTNORM']).values_list(
                            'ExchangePointID', flat=True)
                        Countries_list = Countries.objects.filter(
                            Country_code__in=PCCNTR_ExchP.objects.filter(ExchangePointID__in=EPID_2).values_list(
                                'ExchangePointCountry', flat=True).distinct()).values_list('Name_RUS',
                                                                                           flat=True).distinct()
                        if country in Countries_list:
                            orders_with_requests_ep = Requests.objects.filter(OrderID=order['pk']).values_list(
                                'ExchangePointID', flat=True)
                            for exchp in EPID:
                                if exchp in orders_with_requests_ep:
                                    request_param += 1
                            orders_for_board[order['pk']] = {'num': order['pk'],
                                                             "ExchangeType": ExchangeType[0]['Name_RUS'],
                                                             "SendAmount": str(order['SendAmount']) + " " + str(
                                                                 ExchangeType[0]['SendCurrencyISO']),
                                                             "ReceiveAmount": str(order['ReceiveAmount']) + " " + str(
                                                                 ExchangeType[0]['ReceiveCurrencyISO']),
                                                             "SendTransferType": SendTransferType,
                                                             "ReceiveTransferType": ReceiveTransferType,
                                                             "FinOfficeFrom": order['FinOfficeFrom'],
                                                             "FinOfficeTo": order['FinOfficeTo'],
                                                             "OrderDate": order['OrderDate'],
                                                             "TimeInterval": order["TimeInterval"],
                                                             "Country": country,
                                                             "City": city,
                                                             "DeliveryType": order['DeliveryType'],
                                                             "Comment": order['Comment'],
                                                             'OrderLimit': order['OrderLimit'],
                                                             'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                                             'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                                             'Status': order['Status'],
                                                             'request_param': request_param
                                                             }

                            break

        else:
            work_param = 0
            if user_pccntr.ExchangePointOpenHours_Workingdays != '':
                OpenHours_Workingdays = str(user_pccntr.ExchangePointOpenHours_Workingdays)
                open_hours_workdays = OpenHours_Workingdays[
                                      OpenHours_Workingdays.find('с') + 3:OpenHours_Workingdays.find('д') - 1].strip()
                # open_hours_workdays = datetime.strptime(open_hours_workdays, '%H:%M')
                close_hours_workdays = OpenHours_Workingdays[OpenHours_Workingdays.find('д') + 3:].strip()
                # close_hours_workdays = datetime.strptime(close_hours_workdays, '%H:%M')
            else:
                open_hours_workdays = ''
                close_hours_workdays = ''

            if user_pccntr.ExchangePointOpenHours_Weekends != '':
                OpenHours_Weekends = str(user_pccntr.ExchangePointOpenHours_Weekends)
                open_hours_weekends = OpenHours_Weekends[
                                      OpenHours_Weekends.find('с') + 3:OpenHours_Weekends.find('д') - 1].strip()
                # open_hours_weekends = datetime.strptime(open_hours_weekends, '%H:%M')
                close_hours_weekends = OpenHours_Weekends[OpenHours_Weekends.find('д') + 3:].strip()
                # close_hours_weekends = datetime.strptime(close_hours_weekends, '%H:%M')
            else:
                open_hours_weekends = ''
                close_hours_weekends = ''

            if order['OrderDate'].weekday() == 0:
                if user_pccntr.Monday == 1 and open_hours_workdays != '' and close_hours_workdays != '':
                    open_hour = int(open_hours_workdays[:open_hours_workdays.find(":")])
                    close_hour = int(close_hours_workdays[:close_hours_workdays.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 1:
                if user_pccntr.Tuesday == 1 and open_hours_workdays != '' and close_hours_workdays != '':
                    open_hour = int(open_hours_workdays[:open_hours_workdays.find(":")])
                    close_hour = int(close_hours_workdays[:close_hours_workdays.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 2:
                if user_pccntr.Wednesday == 1 and open_hours_workdays != '' and close_hours_workdays != '':
                    open_hour = int(open_hours_workdays[:open_hours_workdays.find(":")])
                    close_hour = int(close_hours_workdays[:close_hours_workdays.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 3:
                if user_pccntr.Thursday == 1 and open_hours_workdays != '' and close_hours_workdays != '':
                    open_hour = int(open_hours_workdays[:open_hours_workdays.find(":")])
                    close_hour = int(close_hours_workdays[:close_hours_workdays.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 4:
                if user_pccntr.Friday == 1 and open_hours_workdays != '' and close_hours_workdays != '':
                    open_hour = int(open_hours_workdays[:open_hours_workdays.find(":")])
                    close_hour = int(close_hours_workdays[:close_hours_workdays.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 5:
                if user_pccntr.Saturday == 1 and open_hours_weekends != '' and close_hours_weekends != '':
                    open_hour = int(open_hours_weekends[:open_hours_weekends.find(":")])
                    close_hour = int(close_hours_weekends[:close_hours_weekends.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            elif order['OrderDate'].weekday() == 6:
                if user_pccntr.Sunday == 1 and open_hours_weekends != '' and close_hours_weekends != '':
                    open_hour = int(open_hours_weekends[:open_hours_weekends.find(":")])
                    close_hour = int(close_hours_weekends[:close_hours_weekends.find(":")])
                    deal_start = int(str(order["TimeInterval"])[:str(order["TimeInterval"]).find(':')])
                    deal_end = deal_start + 1
                    if (open_hour <= deal_start) and (close_hour >= deal_end):
                        work_param += 1

            print(work_param)
            if work_param != 0:
                Min_Max_PrftNorms = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code,
                                                                 ExchangeTransferID=ExchangeType[0]['pk'],
                                                                 ExchangePointID__in=EPID).values('ExchTOAmount_Min',
                                                                                                  'ExchTOAmount_Max',
                                                                                                  'EP_PRFTNORM').distinct()
                for Min_Max_PrftNorm in Min_Max_PrftNorms:
                    # prft_norm = [Min_Max_PrftNorm]
                    if order['ReceiveAmount'] is not None and order['ReceiveAmount'] >= Min_Max_PrftNorm[
                        'ExchTOAmount_Min'] and order['ReceiveAmount'] <= Min_Max_PrftNorm['ExchTOAmount_Max'] and \
                            order['pk'] not in list(orders_for_board.keys()):
                        # print(1)
                        Countries_list = Countries.objects.filter(Country_code__in=PCCNTR_ExchP.objects.filter(ExchangePointID__in=EPID).values_list(
                                'ExchangePointCountry', flat=True).distinct()).values_list('Name_RUS',
                                                                                           flat=True).distinct()
                        if country in Countries_list:
                            orders_with_requests_ep = Requests.objects.filter(OrderID=order['pk']).values_list(
                                'ExchangePointID', flat=True)
                            for exchp in EPID:
                                if exchp in orders_with_requests_ep:
                                    request_param += 1
                            orders_for_board[order['pk']] = {'num': order['pk'],
                                                             "ExchangeType": ExchangeType[0]['Name_RUS'],
                                                             "SendAmount": str(order['SendAmount']) + " " + str(
                                                                 ExchangeType[0]['SendCurrencyISO']),
                                                             "ReceiveAmount": str(order['ReceiveAmount']) + " " + str(
                                                                 ExchangeType[0]['ReceiveCurrencyISO']),
                                                             "SendTransferType": SendTransferType,
                                                             "ReceiveTransferType": ReceiveTransferType,
                                                             "FinOfficeFrom": order['FinOfficeFrom'],
                                                             "FinOfficeTo": order['FinOfficeTo'],
                                                             "OrderDate": order['OrderDate'],
                                                             "TimeInterval": order["TimeInterval"],
                                                             "Country": country,
                                                             "City": city,
                                                             "DeliveryType": order['DeliveryType'],
                                                             "Comment": order['Comment'],
                                                             'OrderLimit': order['OrderLimit'],
                                                             'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                                             'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                                             'Status': order['Status'],
                                                             'request_param': request_param
                                                             }
                            break


                    elif order['SendAmount'] is not None:
                        # print(2)
                        opertype = \
                        ExchangeID.objects.filter(pk=order['ExchangeID']).values_list('OperTypes', flat=True)[0]
                        # print(opertype)
                        OPRTs = []
                        if ';' in opertype:
                            while ';' in opertype:
                                oprt = opertype[:opertype.find(";")].strip()
                                OPRTs.append(oprt)
                                opertype = opertype[opertype.find(";") + 1:].strip()
                            OPRTs.append(opertype.strip())
                        else:
                            OPRTs.append(opertype.strip())
                        # print(OPRTs)
                        if len(OPRTs) == 1:
                            currency_value = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                  FinOfficeFrom=order['FinOfficeFrom'],
                                                                                  FinOfficeTo=order['FinOfficeTo'],
                                                                                  QuotesRC=
                                                                                  PCCNTR_OperTypes.objects.filter(
                                                                                      PCCNTR=pcc_name.PCCNTR_code,
                                                                                      OperType=OPRTs[0]).values_list(
                                                                                      'QuotesRC', flat=True)[
                                                                                      0]).values_list('Value',
                                                                                                      flat=True)[0])
                            ReceiveAmount = round(float(order['SendAmount']) * currency_value, 2)
                            # print(float(order['SendAmount']))
                            # print(currency_value)
                            # print(ReceiveAmount)

                        elif len(OPRTs) == 2:
                            currency_value_1 = float(Currency_source.objects.filter(OperType=OPRTs[0],
                                                                                    FinOfficeFrom=order[
                                                                                        'FinOfficeFrom'],
                                                                                    FinOfficeTo='TRC20',
                                                                                    QuotesRC=
                                                                                    PCCNTR_OperTypes.objects.filter(
                                                                                        PCCNTR=pcc_name.PCCNTR_code,
                                                                                        OperType=OPRTs[0]).values_list(
                                                                                        'QuotesRC', flat=True)[
                                                                                        0]).values_list('Value',
                                                                                                        flat=True)[
                                                         0])
                            currency_value_2 = float(Currency_source.objects.filter(OperType=OPRTs[1],
                                                                                    FinOfficeFrom='TRC20',
                                                                                    FinOfficeTo=order['FinOfficeTo'],
                                                                                    QuotesRC=
                                                                                    PCCNTR_OperTypes.objects.filter(
                                                                                        PCCNTR=pcc_name.PCCNTR_code,
                                                                                        OperType=OPRTs[1]).values_list(
                                                                                        'QuotesRC', flat=True)[
                                                                                        0]).values_list('Value',
                                                                                                        flat=True)[
                                                         0])
                            ReceiveAmount = round(float(order['SendAmount']) * currency_value_1 * currency_value_2, 2)
                            # print(float(order['SendAmount']))
                            # print(currency_value_1)
                            # print(currency_value_2)
                            # print(ReceiveAmount)
                        if ReceiveAmount >= Min_Max_PrftNorm['ExchTOAmount_Min'] and ReceiveAmount <= Min_Max_PrftNorm[
                            'ExchTOAmount_Max'] and order['pk'] not in list(orders_for_board.keys()):
                            Countries_list = Countries.objects.filter(
                                Country_code__in=PCCNTR_ExchP.objects.filter(ExchangePointID__in=EPID).values_list(
                                    'ExchangePointCountry', flat=True).distinct()).values_list('Name_RUS',
                                                                                               flat=True).distinct()
                            if country in Countries_list:
                                orders_with_requests_ep = Requests.objects.filter(OrderID=order['pk']).values_list(
                                    'ExchangePointID', flat=True)
                                for exchp in EPID:
                                    if exchp in orders_with_requests_ep:
                                        request_param += 1
                                orders_for_board[order['pk']] = {'num': order['pk'],
                                                                 "ExchangeType": ExchangeType[0]['Name_RUS'],
                                                                 "SendAmount": str(order['SendAmount']) + " " + str(
                                                                     ExchangeType[0]['SendCurrencyISO']),
                                                                 "ReceiveAmount": str(
                                                                     order['ReceiveAmount']) + " " + str(
                                                                     ExchangeType[0]['ReceiveCurrencyISO']),
                                                                 "SendTransferType": SendTransferType,
                                                                 "ReceiveTransferType": ReceiveTransferType,
                                                                 "FinOfficeFrom": order['FinOfficeFrom'],
                                                                 "FinOfficeTo": order['FinOfficeTo'],
                                                                 "OrderDate": order['OrderDate'],
                                                                 "TimeInterval": order["TimeInterval"],
                                                                 "Country": country,
                                                                 "City": city,
                                                                 "DeliveryType": order['DeliveryType'],
                                                                 "Comment": order['Comment'],
                                                                 'OrderLimit': order['OrderLimit'],
                                                                 'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                                                 'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                                                 'Status': order['Status'],
                                                                 'request_param': request_param
                                                                 }
                                break

    if user_type != 'Партнер' and user_type != 'Клиент':
        ExchangeName = urllib.parse.unquote(ExchangeName)
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    cache.set('orders_for_board', orders_for_board)
    # print(orders_for_board)
    context = {
        'title': 'Объявления',
        "Orders": orders_for_board,
        "ContactType": usertype,
        # 'orders_with_requests_id': list(orders_with_requests_id),
        # 'orders_with_requests_ep': list(orders_with_requests_ep),
        # 'EPID': list(EPID),
        # 'EP_with_requests': list(set(EPID) & set (orders_with_requests_ep))
    }
    # print(list(orders_with_requests_ep))
    # print(list(EPID))
    # print(list(set(EPID) & set (orders_with_requests_ep)))
    # print(list(set(EPID) & set (orders_with_requests_ep)) in list(EPID))
    return render(request, 'testsite/P2Pmarket_Bulletin_board.html', context=context)

#
def P2Pmarket_Deal_board(request): # добавить фильтр на дату и время сделки
    # global user_type, ExchangeName, orders_for_board
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    username = request.user
    user = Users.objects.filter(TG_Contact=username).values('Name', 'ACTIVE', 'ContactType')
    orders_for_board = {}
    status = ['План']
    if user_type == 'Клиент':
        #print(1)
        Order_for_board = (Orders.objects.filter(TG_Contact=username, Status__in=status)
                                    .values("pk", "ExchangeID","SendAmount","ReceiveAmount",
                                           "FinOfficeFrom","FinOfficeTo","OrderDate",
                                           "TimeInterval","Country", "City",
                                           "DeliveryType","Comment", 'OrderLimit',
                                           'PriceType', 'Status').order_by("-CreatedDate"))
        # orders_with_requests = []

    elif user_type == 'Партнер':
        #print(2)
        pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR', 'ContactType',
                                                                             'ExchangePointID')  # Пользователь-Код Центра прибыли и затрат связь
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])  # Наименование Центра прибыли и затрат

        Deal_Orders = Deals.objects.filter(PCCNTR=pcc_name).values_list('OrderID', flat=True)
        Order_for_board = Orders.objects.filter(pk__in=Deal_Orders).values(
            "pk", "ExchangeID", "SendAmount", "SendTransferType",'ReceiveTransferType',
            "ReceiveAmount", "FinOfficeFrom", "FinOfficeTo", "OrderDate", "TimeInterval",
            "Country", "City", "DeliveryType", "Comment", 'OrderLimit', 'PriceType', 'Status').order_by("-CreatedDate")

    elif user_type == 'Организатор':
        #print(3)
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',flat=True)
        Deal_Orders = list(Deals.objects.filter(ExchangePointID__in=EPID).values_list('OrderID', flat=True))
        Order_for_board = Orders.objects.filter(pk__in=Deal_Orders).values(
            "pk", "ExchangeID", "SendAmount",
            "ReceiveAmount", "FinOfficeFrom", 'FinOfficeTo',
            "OrderDate", "TimeInterval","Country", "City", "DeliveryType",
            "Comment", 'OrderLimit', 'PriceType', "Status").order_by("-CreatedDate")

    else:
        #print(4)
        ExchangeName = urllib.parse.unquote(ExchangeName)
        EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID', flat=True)
        Deal_Orders = list(Deals.objects.filter(ExchangePointID__in=EPID).values_list('OrderID', flat=True))
        Order_for_board = Orders.objects.filter(pk__in=Deal_Orders).values(
            "pk", "ExchangeID", "SendAmount",
            "ReceiveAmount", "FinOfficeFrom", 'FinOfficeTo',
            "OrderDate", "TimeInterval", "Country", "City", "DeliveryType",
            "Comment", 'OrderLimit', 'PriceType', "Status").order_by("-CreatedDate")


    for order in Order_for_board:
        # print(order)

        ExchangeType = ExchangeID.objects.filter(pk=order['ExchangeID']).values('pk',"Name_RUS", "SendCurrencyISO",
                                                                                    "ReceiveCurrencyISO",
                                                                                    "SendTransferType",
                                                                                    'ReceiveTransferType')
        if ExchangeType[0]['SendTransferType'] == "CRP":
            SendTransferType = "Перевод по сети блокчейн"
        elif ExchangeType[0]['SendTransferType'] == "CRD":
            SendTransferType = "Карточный перевод"
        elif ExchangeType[0]['SendTransferType'] == "CSH":
            SendTransferType = "Наличные"

        if ExchangeType[0]['ReceiveTransferType'] == "CRP":
            ReceiveTransferType = "Перевод по сети блокчейн"
        elif ExchangeType[0]['ReceiveTransferType'] == "CRD":
            ReceiveTransferType = "Карточный перевод"
        elif ExchangeType[0]['ReceiveTransferType'] == "CSH":
            ReceiveTransferType = "Наличные"


        city = Cities.objects.filter(City_code=order['City']).values('Name_RUS')[0]['Name_RUS']
        country = Countries.objects.filter(Country_code=order['Country']).values('Name_RUS')[0]['Name_RUS']

        Deal_data = Deals.objects.get(OrderID=order['pk'])
        Request_data = Requests.objects.get(pk=Deal_data.RequestID)
        orders_for_board[order['pk']] = {'num': Deal_data.pk, "ExchangeType": ExchangeType[0]['Name_RUS'],
                                             "SendAmount": str(Request_data.SendAmount) + " " + str(
                                                 ExchangeType[0]['SendCurrencyISO']),
                                             "ReceiveAmount": str(Request_data.ReceiveAmount) + " " + str(
                                                 ExchangeType[0]['ReceiveCurrencyISO']),
                                             "SendTransferType": SendTransferType,
                                             "ReceiveTransferType": ReceiveTransferType,
                                             "FinOfficeFrom": order['FinOfficeFrom'],
                                             "FinOfficeTo": order['FinOfficeTo'],
                                             "OrderDate": order['OrderDate'],
                                             "TimeInterval": order["TimeInterval"],
                                             "Country": country,
                                             "City": city,
                                             "DeliveryType": order['DeliveryType'],
                                             "Comment": order['Comment'],
                                             'OrderLimit': order['OrderLimit'],
                                             'SendCurrencyISO': ExchangeType[0]['SendCurrencyISO'],
                                             'ReceiveCurrencyISO': ExchangeType[0]['ReceiveCurrencyISO'],
                                             'Status': order['Status'],
                                             }


    if user_type != 'Партнер' and user_type != 'Клиент':
        ExchangeName = urllib.parse.unquote(ExchangeName)
        usertype = ExchangeName
    else:
        usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
            'ContactType_code']
    cache.set('orders_for_board', orders_for_board)
    # print(orders_for_board)
    context = {
        'title': 'Сделки',
        "Orders": orders_for_board,
        "ContactType": usertype,
        # 'orders_with_requests_id': list(orders_with_requests_id),
        # 'orders_with_requests_ep': list(orders_with_requests_ep),
        # 'EPID': list(EPID),
        # 'EP_with_requests': list(set(EPID) & set (orders_with_requests_ep))
    }
    # print(list(orders_with_requests_ep))
    # print(list(EPID))
    # print(list(set(EPID) & set (orders_with_requests_ep)))
    # print(list(set(EPID) & set (orders_with_requests_ep)) in list(EPID))
    return render(request, 'testsite/P2Pmarket_Deal_board.html', context=context)

#
def P2Pmarket_Bulletin_board_delete_confirm(request, num):
    # global user_type, orders_for_board
    orders_for_board = cache.get('orders_for_board')
    return render(request, 'testsite/P2Pmarket_Bulletin_board_delete_confirm.html',
                  context={'title': 'Подтверждение удаления заявки на обмен', 'Order': orders_for_board[num],
                           'num': num})

#
def P2Pmarket_Bulletin_board_delete_final(request, num):
    # global user_type
    # user_type = cache.get('user_type')
    order = Orders.objects.get(pk=num)
    order.Status = 'Отменен'
    order.save()
    reqs = Requests.objects.filter(OrderID=num).values_list('pk', flat=True)
    for req in reqs:
        requests_to_delete = Requests.objects.get(pk=req)
        requests_to_delete.status = 'Отменен'
        requests_to_delete.save()
        DealReserve_data = DealReserve.objects.get(PCCNTR=requests_to_delete.PCCNTR, OrderID=requests_to_delete.OrderID,
                                                   RequestID=requests_to_delete.pk)
        PCCNTR_data = PCCNTR.objects.get(PCCNTR_code=requests_to_delete.PCCNTR)
        PCCNTR_data.Reserve = PCCNTR_data.Reserve - DealReserve_data.Reserve_Amount
        DealReserve.objects.filter(PCCNTR=requests_to_delete.PCCNTR, OrderID=requests_to_delete.OrderID,
                                   RequestID=requests_to_delete.pk).delete()
        PCCNTR_data.save()
        partner_contacts = Users_PCCNTR.objects.get(PCCNTR=requests_to_delete.PCCNTR, ContactType='PART')
        Notifications.objects.create(TG_Contact=partner_contacts.TG_Contact, ContactType='PART',
                                     PCCNTR=requests_to_delete.PCCNTR, ExchangePointID='-',
                                     Text='Заявке на обмен №' + str(
                                         requests_to_delete.OrderID) + ' была удалена клиентом')
        mail_subject = 'Удаление заявки на обмен'
        email = User.objects.filter(username=partner_contacts.TG_Contact).values_list('email', flat=True)[0]
        to_email = email
        msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
        html_content = get_template(
            'testsite/send_notification_to_PCCNTR_order_delete.html').render({
            'user': partner_contacts.TG_Contact,
            'OrderNum': requests_to_delete.OrderID,
        })
        msg.attach_alternative(html_content, "text/html")
        res = msg.send()

        org_contacts = Users_PCCNTR.objects.get(PCCNTR=requests_to_delete.PCCNTR, ContactType='ORG',
                                                ExchangePointID__contains=requests_to_delete.ExchangePointID)
        if org_contacts.TG_Contact != partner_contacts.TG_Contact:
            Notifications.objects.create(TG_Contact=org_contacts.TG_Contact, ContactType='ORG',
                                         PCCNTR=requests_to_delete.PCCNTR,
                                         ExchangePointID=requests_to_delete.ExchangePointID,
                                         Text='Заявке на обмен №' + str(
                                             requests_to_delete.OrderID) + ' была удалена клиентом')
            mail_subject = 'Удаление заявки на обмен'
            email = User.objects.filter(username=org_contacts.TG_Contact).values_list('email', flat=True)[0]
            to_email = email
            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
            html_content = get_template(
                'testsite/send_notification_to_PCCNTR_order_delete.html').render({
                'user': org_contacts.TG_Contact,
                'OrderNum': requests_to_delete.OrderID,
            })
            msg.attach_alternative(html_content, "text/html")
            res = msg.send()

        job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
        empl_contacts = (Users_PCCNTR.objects.filter(PCCNTR=requests_to_delete.PCCNTR,
                                                     ContactType__in=job_positions,
                                                     ExchangePointID__contains=requests_to_delete.ExchangePointID)
                         .values('TG_Contact', 'ContactType'))
        for empl in empl_contacts:
            if empl['TG_Contact'] != partner_contacts.TG_Contact and empl[
                'TG_Contact'] != org_contacts.TG_Contact:
                Notifications.objects.create(TG_Contact=empl['TG_Contact'],
                                             ContactType=empl['ContactType'],
                                             PCCNTR=requests_to_delete.PCCNTR,
                                             ExchangePointID=requests_to_delete.ExchangePointID,
                                             Text='Заявке на обмен №' + str(
                                                 requests_to_delete.OrderID) + ' была удалена клиентом')
                mail_subject = 'Удаление заявки на обмен'
                email = User.objects.filter(username=empl['TG_Contact']).values_list('email', flat=True)[0]
                to_email = email
                msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
                html_content = get_template(
                    'testsite/send_notification_to_PCCNTR_order_delete.html').render({
                    'user': empl['TG_Contact'],
                    'OrderNum': requests_to_delete.OrderID,
                })
                msg.attach_alternative(html_content, "text/html")
                res = msg.send()
    cache.delete('orders_for_board')
    return redirect('P2Pmarket_Bulletin_board')

#
def P2Pmarket_Choose_Request(request, num):
    # global user_type, ExchangeName, orders_for_board
    # user_type = cache.get('user_type')
    # ExchangeName = cache.get('ExchangeName')
    orders_for_board = cache.get('orders_for_board')
    Requests_data = Requests.objects.filter(OrderID=num, Active=True).values('pk', 'ExchangePointID', 'SendAmount', 'ReceiveAmount')
    if 'None' in orders_for_board[num]['SendAmount']:
        Requests_data = Requests_data.order_by('SendAmount')
    else:
        Requests_data = Requests_data.order_by('-ReceiveAmount')

    for request_data in Requests_data:
        request_data['ExchangePointName'] = PCCNTR_ExchP.objects.get(ExchangePointID=request_data['ExchangePointID']).ExchangePointName
        request_data['ExchangeRate'] = round(request_data['ReceiveAmount']/request_data['SendAmount'], 5)

    Not_active_requests = len(Requests.objects.filter(OrderID=num, Active=False).values_list('pk', flat=True))
    cache.delete('orders_for_board')
    context = {
        'title': 'Предложения',
        'Order': orders_for_board[num],
        'Requests': Requests_data,
        'Not_active_requests': Not_active_requests,
        'num': num
    }
    return render(request, 'testsite/P2Pmarket_Choose_Request.html', context=context)

#
def P2Pmarket_Exchange_request(request, num):
    # global user_type, ExchangeName, orders_for_board
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    orders_for_board = cache.get('orders_for_board')
    order = orders_for_board[num]
    # print(user_type)

    if user_type == "Партнер":
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        ExchangePointIDs = list(PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointCity__contains=Cities.objects.filter(Name_RUS = order['City']).values_list('City_code', flat=True)[0]).values_list('ExchangePointID', flat=True))
        EP_Profit_Norm = EP_ExchangeID.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointID__in=ExchangePointIDs,
                                                      ExchangeTransferID=ExchangeID.objects.filter(Name_RUS=order['ExchangeType']).values_list('pk', flat=True)[0]).values(
            'PCCNTR', 'ExchangePointID', 'ExchTOAmount_Min', 'ExchTOAmount_Max', 'EP_PRFTNORM').distinct()

    else:
        ExchangeName = urllib.parse.unquote(ExchangeName)
        # print(ExchangeName)
        EPID = list(PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName, ExchangePointCity__contains=Cities.objects.filter(Name_RUS = order['City']).values_list('City_code', flat=True)[0]).values_list('ExchangePointID', flat=True).order_by('ExchangePointID'))
        pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ExchangePointID__contains='; '.join(EPID)).values('TG_Contact', 'PCCNTR')
        if len(pcc) == 0:
            pcc = Users_PCCNTR.objects.filter(TG_Contact=request.user, ExchangePointID__in=EPID).values('TG_Contact', 'PCCNTR')
        pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
        EP_Profit_Norm = EP_ExchangeID.objects.filter(ExchangePointID__in=EPID, ExchangeTransferID=ExchangeID.objects.filter(
                                                              Name_RUS=order['ExchangeType']).values_list('pk',flat=True)[0]).values('PCCNTR', 'ExchangePointID', 'ExchTOAmount_Min', 'ExchTOAmount_Max', 'EP_PRFTNORM').distinct()
    # print(EPID)
    # print(EP_Profit_Norm)
    currency_to_sell = ExchangeID.objects.filter(Name_RUS=order['ExchangeType']).values_list('SendCurrencyISO', flat=True)[0]
    currency_to_buy = ExchangeID.objects.filter(Name_RUS=order['ExchangeType']).values_list('ReceiveCurrencyISO', flat=True)[0]
    if 'None' in order['SendAmount']:
        amount_type = 'receive'
        amount = int(order['ReceiveAmount'][:order['ReceiveAmount'].find(' ')].strip())
    elif 'None' in order['ReceiveAmount']:
        amount_type = 'send'
        amount = int(order['SendAmount'][:order['SendAmount'].find(' ')].strip())

    ### Новый расчет
    rate_calculator = RateCalc(order=order, pcc_name=pcc_name, amount=amount, amount_type=amount_type)
    currency_full_value, exchange_rate = rate_calculator.calculate_rate()

    if 'None' in order['ReceiveAmount']:
        amount = currency_full_value
    max_percent = 0
    for profit_norm in EP_Profit_Norm:
        if amount >= profit_norm['ExchTOAmount_Min'] and amount <= profit_norm['ExchTOAmount_Max']:
            # print(profit_norm)
            Norm_Prib = profit_norm['EP_PRFTNORM']
            Norm_Prib_Name_1 = []
            Norm_Prib_Name_2 = []
            Norm_Prib_Percent = []
            if ';' in Norm_Prib:
                while ";" in Norm_Prib:
                    N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
                    Name = N_P[:N_P.find(' ')].strip()
                    Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
                    Name_1 = Name[:Name.find("-")].strip()
                    Norm_Prib_Name_1.append(Name_1)
                    Name_2 = Name[Name.find("-") + 1:].strip()
                    Norm_Prib_Name_2.append(Name_2)
                    Norm_Prib_Percent.append(Percent)
                    Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
                Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                Name_1 = Name[:Name.find("-")].strip()
                Norm_Prib_Name_1.append(Name_1)
                Name_2 = Name[Name.find("-") + 1:].strip()
                Norm_Prib_Name_2.append(Name_2)
                Norm_Prib_Percent.append(Percent)
            else:
                Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
                Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
                Name_1 = Name[:Name.find("-")].strip()
                Norm_Prib_Name_1.append(Name_1)
                Name_2 = Name[Name.find("-") + 1:].strip()
                Norm_Prib_Name_2.append(Name_2)
                Norm_Prib_Percent.append(Percent)

            for i in range(len(Norm_Prib_Name_1)):
                if amount >= float(Norm_Prib_Name_1[i]) and amount <= float(Norm_Prib_Name_2[i]):
                    if max_percent < float(Norm_Prib_Percent[i]):
                        max_percent = float(Norm_Prib_Percent[i])
                        EP = profit_norm['ExchangePointID']

    balance_amount = int(pcc_name.Balance - pcc_name.Reserve)

    if 'None' in order['ReceiveAmount'] and max_percent != 0:  # send - считаем сколько отдать
        # print(1)
        exchange_rate = exchange_rate * (1 - max_percent / 100)
        currency_full_value = int(order['SendAmount'][:order['SendAmount'].find(' ')].strip()) * exchange_rate
    elif max_percent != 0:  # receive - считаем сколько взять
        # print(2)
        exchange_rate = exchange_rate * (1 - max_percent / 100)
        currency_full_value = int(order['ReceiveAmount'][:order['ReceiveAmount'].find(' ')].strip()) / exchange_rate

    if request.method == 'POST':
        form = Exchangerequest(request.POST)
        if form.is_valid():
            order_db = Orders.objects.get(pk=num)
            user = order_db.TG_Contact
            if amount_type == 'receive':
                if currency_to_sell != 'USDT' and currency_to_buy != 'USDT':
                    sumusdt_send = int(order_db.ReceiveAmount * float(Currency_source.objects.get(OperType= str(currency_to_buy) + " => USDT",
                                                                            FinOfficeFrom='Наличные',
                                                                            FinOfficeTo='TRC20',
                                                                            QuotesRC='GARALL').Value))
                    sumusdt_receive = int(form.cleaned_data.get('amount') * float(Currency_source.objects.get(OperType=str(currency_to_sell) + " => USDT",
                                                    FinOfficeFrom='Наличные',
                                                    FinOfficeTo='TRC20',
                                                    QuotesRC='GARALL').Value))
                elif currency_to_buy == 'USDT':
                    sumusdt_send = order_db.ReceiveAmount
                    sumusdt_receive = order_db.ReceiveAmount
                else:
                    sumusdt_send = int(form.cleaned_data.get('amount'))
                    sumusdt_receive = int(form.cleaned_data.get('amount'))

                if currency_to_sell != 'EUR' and currency_to_buy != 'EUR':
                    sumeur_send = int(sumusdt_send * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                          FinOfficeFrom='TRC20',
                                                                                          FinOfficeTo='Наличные',
                                                                                          QuotesRC='GARALL').Value))
                    sumeur_receive = int(sumusdt_receive * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                             FinOfficeFrom='TRC20',
                                                                                             FinOfficeTo='Наличные',
                                                                                             QuotesRC='GARALL').Value))
                elif currency_to_buy == 'EUR':
                    sumeur_send = int(order_db.ReceiveAmount)
                    sumeur_receive = int(order_db.ReceiveAmount)
                else:
                    sumeur_send = int(form.cleaned_data.get('amount'))
                    sumeur_receive = int(form.cleaned_data.get('amount'))

                if int(sumusdt_receive*0.01) > balance_amount:
                    error = 'Недостаточно средств для формирования предложения. Необзодимо пополнить счет на ' + str(int(sumusdt_receive*0.01) - balance_amount) + ' USDT'
                    context = {
                        'title': 'Предложение обменника', 'Order': order, 'error':error,
                        'currency_full_value': round(currency_full_value, 2)
                        , 'currency_value': exchange_rate, 'amount_type': amount_type, 'balance': balance_amount,
                        'currency_to_buy': currency_to_buy
                        , 'currency_to_sell': currency_to_sell,
                        'form': form, 'max_percent': int(max_percent)
                    }
                    return render(request, 'testsite/P2Pmarket_Exchange_request.html', context=context)

                Requests.objects.create(OrderID=num, PCCNTR=pcc_name.PCCNTR_code,
                                        ReceiveCurrencyISO=currency_to_buy
                                        , SendCurrencyISO=currency_to_sell,
                                        SendAmount=form.cleaned_data.get('amount')
                                        , ReceiveAmount=order_db.ReceiveAmount, Status='Создан'
                                        , ExchangeID=order_db.ExchangeID, TG_Contact=request.user, ExchangePointID=EP,
                                        receiveinUSDT = sumusdt_receive, sendinUSDT = sumusdt_send,
                                        receiveinEUR = sumeur_receive, sendinEUR = sumeur_send,
                                        ExchRateEURUSDT = round(sumusdt_receive/sumeur_send,5), ExchRateUSDTEUR=round(sumeur_receive/sumusdt_send,5))
                Notifications.objects.create(TG_Contact=user, ContactType='CLI', PCCNTR='-', ExchangePointID='-',
                                             Text='Обменник ' + str(
                                                 PCCNTR_ExchP.objects.filter(ExchangePointID=EP).values_list(
                                                     'ExchangePointName', flat=True)[
                                                     0]) + ' направил предложение по сделке '
                                                  + str(order['ExchangeType']) + '<br> Курс: 1 ' + str(
                                                 currency_to_sell) + ' = ' + str(
                                                 form.cleaned_data.get('exchange_rate')) + ' ' + str(currency_to_buy)
                                                  + '<br> Сумма сделки: ' + str(form.cleaned_data.get('amount')) + ' ' + str(currency_to_sell) + ' = ' + str(order_db.ReceiveAmount) + ' ' + str(currency_to_buy))
                DealReserve.objects.create(PCCNTR=pcc_name.PCCNTR_code, Reserve_Amount = int(sumusdt_receive*0.01), OrderID = num,
                                           RequestID = Requests.objects.get(OrderID=num, ExchangePointID = EP, receiveinUSDT=sumusdt_receive).pk)
                pcc_name.Reserve = pcc_name.Reserve + int(sumusdt_receive*0.01)
                pcc_name.save()
            elif amount_type == 'send':
                if currency_to_sell != 'USDT' and currency_to_buy != 'USDT':
                    sumusdt_send = int(order_db.SendAmount * float(Currency_source.objects.get(OperType= str(currency_to_sell) + " => USDT",
                                                                            FinOfficeFrom='Наличные',
                                                                            FinOfficeTo='TRC20',
                                                                            QuotesRC='GARALL').Value))
                    sumusdt_receive = int(form.cleaned_data.get('amount') * float(
                        Currency_source.objects.get(OperType=str(currency_to_buy) + " => USDT",
                                                    FinOfficeFrom='Наличные',
                                                    FinOfficeTo='TRC20',
                                                    QuotesRC='GARALL').Value))
                elif currency_to_sell == 'USDT':
                    sumusdt_send = int(order_db.SendAmount)
                    sumusdt_receive = int(order_db.SendAmount)
                else:
                    sumusdt_send = int(form.cleaned_data.get('amount'))
                    sumusdt_receive = int(form.cleaned_data.get('amount'))

                if currency_to_sell != 'EUR' and currency_to_buy != 'EUR':
                    sumeur_send = int(sumusdt_send * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                          FinOfficeFrom='TRC20',
                                                                                          FinOfficeTo='Наличные',
                                                                                          QuotesRC='GARALL').Value))
                    sumeur_receive = int(sumusdt_receive * float(Currency_source.objects.get(OperType="USDT => EUR",
                                                                                             FinOfficeFrom='TRC20',
                                                                                             FinOfficeTo='Наличные',
                                                                                             QuotesRC='GARALL').Value))
                elif currency_to_sell == 'EUR':
                    sumeur_send = int(order_db.SendAmount)
                    sumeur_receive = int(order_db.SendAmount)
                else:
                    sumeur_send = int(form.cleaned_data.get('amount'))
                    sumeur_receive = int(form.cleaned_data.get('amount'))



                if int(sumusdt_receive*0.01) > balance_amount:
                    error = 'Недостаточно средств для формирования предложения. Необзодимо пополнить счет на ' + str(int(sumusdt_receive*0.01) - balance_amount) + ' USDT'
                    context = {
                        'title': 'Предложение обменника', 'Order': order, 'error':error,
                        'currency_full_value': round(currency_full_value, 2)
                        , 'currency_value': exchange_rate, 'amount_type': amount_type, 'balance': balance_amount,
                        'currency_to_buy': currency_to_buy
                        , 'currency_to_sell': currency_to_sell,
                        'form': form, 'max_percent': int(max_percent)
                    }
                    return render(request, 'testsite/P2Pmarket_Exchange_request.html', context=context)
                Requests.objects.create(OrderID=num, PCCNTR=pcc_name.PCCNTR_code,
                                        ReceiveCurrencyISO=currency_to_buy
                                        , SendCurrencyISO=currency_to_sell,
                                        SendAmount=order_db.SendAmount
                                        , ReceiveAmount=form.cleaned_data.get('amount'), Status='Создан'
                                        , ExchangeID=order_db.ExchangeID, TG_Contact=request.user, ExchangePointID=EP,
                                        receiveinUSDT=sumusdt_receive, sendinUSDT=sumusdt_send,
                                        receiveinEUR=sumeur_receive, sendinEUR=sumeur_send,
                                        ExchRateEURUSDT = round(sumusdt_receive/sumeur_send,5), ExchRateUSDTEUR=round(sumeur_receive/sumusdt_send,5))
                Notifications.objects.create(TG_Contact=user, ContactType='CLI', PCCNTR='-', ExchangePointID='-',
                                             Text='Обменник ' + str(
                                                 PCCNTR_ExchP.objects.filter(ExchangePointID=EP).values_list(
                                                     'ExchangePointName', flat=True)[
                                                     0]) + ' направил предложение по сделке '
                                                  + str(order['ExchangeType']) + '<br> Курс: 1 ' + str(
                                                 currency_to_sell) + ' = ' + str(
                                                 form.cleaned_data.get('exchange_rate')) + ' ' + str(currency_to_buy)
                                                  + '<br> Сумма сделки: ' + str(order_db.SendAmount) + ' ' + str(
                                                 currency_to_sell) + ' = ' + str(form.cleaned_data.get('amount')) + ' ' + str(currency_to_buy))
                DealReserve.objects.create(PCCNTR=pcc_name.PCCNTR_code, Reserve_Amount=int(sumusdt_receive*0.01), OrderID=num,
                                           RequestID=Requests.objects.get(OrderID=num, ExchangePointID=EP, sendinUSDT=sumusdt_send).pk)
                pcc_name.Reserve = pcc_name.Reserve + int(sumusdt_receive*0.01)
                pcc_name.save()

            mail_subject = 'Предложение от обменника'
            email = User.objects.filter(username=user).values_list('email', flat=True)[0]
            to_email = email
            msg = EmailMultiAlternatives(mail_subject, '', "ya.maxrov@ya.ru", [to_email])
            html_content = get_template('testsite/send_notification_to_client_request.html').render({
                'user': user,
                'ExchangeName':
                    PCCNTR_ExchP.objects.filter(ExchangePointID=EP).values_list('ExchangePointName', flat=True)[0],
                'DealName': order['ExchangeType'],
            })
            msg.attach_alternative(html_content, "text/html")
            res = msg.send()
            cache.delete('orders_for_board')
            return redirect('P2Pmarket_Bulletin_board')
    else:
        form = Exchangerequest(initial={'exchange_rate': round(exchange_rate,5),
                                        'reverse_exchange_rate': round(1/round(exchange_rate,5),5),
                                                        'amount': round(currency_full_value, 2)})
    context = {
        'title': 'Предложение обменника', 'Order': order, 'currency_full_value': round(currency_full_value, 2)
        , 'currency_value': exchange_rate, 'amount_type': amount_type, 'balance': balance_amount,
        'currency_to_buy': currency_to_buy
        , 'currency_to_sell': currency_to_sell,
        'form': form, 'max_percent': int(max_percent)
    }

    return render(request, 'testsite/P2Pmarket_Exchange_request.html', context=context)

#
def load_cities(request):
    country_name = request.GET.get('COUNTRY')
    country_name = urllib.parse.unquote(country_name)
    country_id = Countries.objects.filter(Name_RUS=country_name).values('Country_code')[0]['Country_code']
    cities = Cities.objects.filter(Country=country_id)
    return render(request, 'testsite/city_options.html', {'cities': cities})

#
def load_cities_num(request, num):
    # global exchange_name
    exchange_name = cache.get('ExchangeName')
    # print(exchange_name)
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    country_name = request.GET.get('ExchPCountries')
    country_name = urllib.parse.unquote(country_name)
    country_id = str(list(Countries.objects.filter(Name_RUS=country_name).values_list('Country_code', flat=True))[0])
    ExchPCities = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=exchange_name,
                                              ExchangePointCountry=country_id).values_list("ExchangePointCity",flat=True)

    cities = []
    for city in ExchPCities:
        while ";" in city:
            city_1 = city[:city.find(';')]
            city = city[city.find(';') + 2:].strip()
            cities.append(Cities.objects.filter(City_code=city_1.strip()).values_list('Name_RUS', flat=True)[0])
    cities.append(Cities.objects.filter(City_code=city.strip()).values_list('Name_RUS', flat=True)[0])

    cities = list(set(cities))
    cities = Cities.objects.filter(Name_RUS__in=cities)
    # print(cities)

    return render(request, 'testsite/city_options_multi.html', {'cities': cities})

def load_cities_text(request, employee_name):
    # global exchange_name
    exchange_name = cache.get('ExchangeName')
    username = request.user
    pcc = Users_PCCNTR.objects.filter(TG_Contact=username).values('TG_Contact', 'PCCNTR')
    pcc_name = PCCNTR.objects.get(PCCNTR_code=pcc[0]['PCCNTR'])
    country_name = request.GET.get('ExchPCountries')
    country_name = urllib.parse.unquote(country_name)
    country_id = str(list(Countries.objects.filter(Name_RUS=country_name).values_list('Country_code', flat=True))[0])
    ExchPCities = PCCNTR_ExchP.objects.filter(PCCNTR=pcc_name.PCCNTR_code, ExchangePointName=exchange_name,
                                            ExchangePointCountry=country_id).values_list("ExchangePointCity",flat=True)
    cities = []
    for city in ExchPCities:
        while ";" in city:
            city_1 = city[:city.find(';')]
            city = city[city.find(';') + 2:].strip()
            cities.append(Cities.objects.filter(City_code=city_1.strip()).values_list('Name_RUS', flat=True)[0])
    cities.append(Cities.objects.filter(City_code=city.strip()).values_list('Name_RUS', flat=True)[0])

    cities = list(set(cities))
    cities = Cities.objects.filter(Name_RUS__in=cities)
    # print(cities)

    return render(request, 'testsite/city_options_multi.html', {'cities': cities})

#
def register2(request):
    # global user_name
    if request.method == 'POST':
        form = AddPersonalInformation(request.POST)
        if form.is_valid():
            username = request.user
            users = Users.objects.filter(TG_Contact=username)
            if len(users) == 0:
                if form.cleaned_data['USERTYPE'] == 'Клиент':
                    Users.objects.create(TG_Contact=username)
                    user_client = Users.objects.get(TG_Contact=username)
                    contacttype = ContactType.objects.filter(Name_RUS=form.cleaned_data['USERTYPE']).values(
                        'ContactType_code')
                    user_client.ContactType = contacttype[0]['ContactType_code']
                    user_client.Surname = form.cleaned_data['Surname']
                    user_client.Name = form.cleaned_data['Name']
                    if str(form.cleaned_data['Otchestvo']) != "":
                        user_client.Otchestvo = form.cleaned_data['Otchestvo']
                    gender = Gender.objects.filter(Name_RUS=form.cleaned_data['GENDER']).values('Gender_code')
                    user_client.GENDER = gender[0]['Gender_code']
                    country = Countries.objects.filter(Name_RUS=form.cleaned_data['COUNTRY']).values('Country_code')
                    user_client.COUNTRY = country[0]['Country_code']
                    city = Cities.objects.filter(Name_RUS=form.cleaned_data['CITY']).values('City_code')
                    user_client.CITY = city[0]['City_code']
                    user_client.Language = form.cleaned_data['Language']
                    user_client.save()
                else:
                    Users.objects.create(TG_Contact=username)
                    Users_PCCNTR.objects.create(TG_Contact=username)
                    user_client = Users.objects.get(TG_Contact=username)
                    user_pccntr = Users_PCCNTR.objects.get(TG_Contact=username)

                    contacttype_pccntr = ContactType.objects.filter(Name_RUS='Партнер').values('ContactType_code')
                    contacttype_client = ContactType.objects.filter(Name_RUS='Клиент').values('ContactType_code')
                    user_client.ContactType = contacttype_client[0]['ContactType_code']
                    user_pccntr.ContactType = contacttype_pccntr[0]['ContactType_code']
                    user_client.Surname = form.cleaned_data['Surname']
                    user_client.Name = form.cleaned_data['Name']
                    if str(form.cleaned_data['Otchestvo']) != "":
                        user_client.Otchestvo = form.cleaned_data['Otchestvo']
                    gender = Gender.objects.filter(Name_RUS=form.cleaned_data['GENDER']).values('Gender_code')
                    user_client.GENDER = gender[0]['Gender_code']
                    country = Countries.objects.filter(Name_RUS=form.cleaned_data['COUNTRY']).values('Country_code')
                    user_client.COUNTRY = country[0]['Country_code']
                    user_pccntr.COUNTRY = country[0]['Country_code']
                    city = Cities.objects.filter(Name_RUS=form.cleaned_data['CITY']).values('City_code')
                    user_client.CITY = city[0]['City_code']
                    user_pccntr.CITY = city[0]['City_code']
                    user_client.Language = form.cleaned_data['Language']
                    user_pccntr.Language = form.cleaned_data['Language']
                    user_client.save()
                    user_pccntr.save()
            if form.cleaned_data['USERTYPE'] == 'Обменник-Партнер':
                return redirect('register_pccntr')
            else:
                return redirect('home', 'CLI')
    else:
        form = AddPersonalInformation()
    return render(request, 'testsite/register2.html', {'form': form, 'title': 'Персональные данные пользователя'})

#
def register_pccntr(request):
    # global user_type, pcc_code
    if request.method == 'POST':
        form = AddPCCNTRName(request.POST)
        if form.is_valid():
            username = request.user
            PCCNTRs = PCCNTR.objects.filter(PCCNTR_name=form.cleaned_data['PCCNTR_name']).all()
            if len(PCCNTRs) == 0:
                PCCNTR.objects.create(PCCNTR_name=form.cleaned_data['PCCNTR_name'])
                pcc = PCCNTR.objects.get(PCCNTR_name=form.cleaned_data['PCCNTR_name'])
                pcc_num = str(pcc.pk)
                pcc_num = pcc_num.zfill(7)
                pcc_code = str('PC1' + pcc_num)
                pcc.PCCNTR_code = pcc_code
                pcc.save()
                user = Users_PCCNTR.objects.get(TG_Contact=username)
                user.PCCNTR = str('PC1' + pcc_num)
                user.save()
                user_type = 'Партнер'
                cache.set('user_type', user_type)
                cache.set('pcc_code', pcc_code)
                return redirect('general_settings_exchange_structure_new_1')
            else:
                error = 'Центр прибыли и затрат с данным наименованием уже зарегистрирован в системе'
                return render(request, 'testsite/register_pccntr.html',
                              {'form': form, 'title': 'Наименование Центра прибыли и затрат', 'param': 0, 'error': error})
    else:
        form = AddPCCNTRName()
    return render(request, 'testsite/register_pccntr.html',
                  {'form': form, 'title': 'Наименование Центра прибыли и затрат', 'param': 0})

#
def feedback(request, num, num2):
    # global checked_username, user_type, ExchangeName, Org_Name
    user_type = cache.get('user_type')
    ExchangeName = cache.get('ExchangeName')
    # checked_username = cache.get('checked_username')
    # Org_Name = cache.get('Org_Name')
    if num == 1:
        if user_type != 'Партнер' and user_type != 'Клиент' :
            ExchangeName = urllib.parse.unquote(ExchangeName)
            usertype = ExchangeName
        else:
            usertype = ContactType.objects.filter(Name_RUS=user_type).values('ContactType_code')[0][
                'ContactType_code']
    elif num == 36 and user_type == 'Организатор':
        usertype = 'ORG'
    elif num == 36 and user_type != 'Организатор':
        usertype = 'EMPL'    
    else:
        usertype = ''

    if request.method == 'POST':
        form = Feedback(num, request.POST)
        if form.is_valid():
            if num == 1 : #Главное меню
                username = request.user

                user2 = User.objects.filter(username=username).values('username', 'email')
                if user_type == 'Клиент':
                    ExchangeName = ''
                    user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                    FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                            Language_code=user[0]['Language'], email=user2[0]['email'],
                                            Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                            Text=form.cleaned_data.get('Text'), Rating=form.cleaned_data.get('Rating'), Page='Главное меню')

                elif user_type == 'Партнер':
                    ExchangeName = ''
                    user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'Surname')
                    user_2 = Users_PCCNTR.objects.filter(TG_Contact=username).values('COUNTRY', 'Language', 'PCCNTR',
                                                                                     "ExchangePointID")
                    FeedBack.objects.create(User=username, Country_code=user_2[0]['COUNTRY'],
                                            Language_code=user_2[0]['Language'], email=user2[0]['email'],
                                            Name=str(user_1[0]['Surname'] + " " + user_1[0]['Name']),
                                            PCCNTR=user_2[0]['PCCNTR'],
                                            ExchangePointID=user_2[0]['ExchangePointID'],
                                            Text=form.cleaned_data.get('Text'),
                                            Rating=form.cleaned_data.get('Rating'), Page='Главное меню')

                elif user_type == 'Организатор':
                    ExchangeName = urllib.parse.unquote(ExchangeName)
                    user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'Surname')
                    EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                                   flat=True).order_by(
                        'ExchangePointID')
                    EPID_str = '; '.join(EPID)
                    user_2 = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType='ORG',
                                                         ExchangePointID=EPID_str).values('COUNTRY', 'Language', 'PCCNTR',
                                                                                          "ExchangePointID")
                    FeedBack.objects.create(User=username, Country_code=user_2[0]['COUNTRY'],
                                            Language_code=user_2[0]['Language'], email=user2[0]['email'],
                                            Name=str(user_1[0]['Surname'] + " " + user_1[0]['Name']),
                                            PCCNTR=user_2[0]['PCCNTR'],
                                            ExchangePointID=user_2[0]['ExchangePointID'],
                                            Text=form.cleaned_data.get('Text'),
                                            Rating=form.cleaned_data.get('Rating'), Page='Главное меню')

                else:
                    job_positions = ['COUR; CUR', 'COUR', 'CUR', 'CUR; COUR']
                    ExchangeName = urllib.parse.unquote(ExchangeName)
                    EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=ExchangeName).values_list('ExchangePointID',
                                                                                                   flat=True)
                    user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'Surname')
                    user_2 = Users_PCCNTR.objects.filter(TG_Contact=username, ContactType__in=job_positions,
                                                         ExchangePointID__in=EPID).values('COUNTRY', 'Language', 'PCCNTR',
                                                                                          "ExchangePointID")
                    FeedBack.objects.create(User=username, Country_code=user_2[0]['COUNTRY'],
                                            Language_code=user_2[0]['Language'], email=user2[0]['email'],
                                            Name=str(user_1[0]['Surname'] + " " + user_1[0]['Name']),
                                            PCCNTR=user_2[0]['PCCNTR'],
                                            ExchangePointID=user_2[0]['ExchangePointID'],
                                            Text=form.cleaned_data.get('Text'),
                                            Rating=form.cleaned_data.get('Rating'), Page='Главное меню')
            elif num == 2: #Ввод email для сброса пароля
                ExchangeName = ''
                try:
                    username = request.user
                    user2 = User.objects.filter(username=username).values('username', 'email')

                    user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                    FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                            Language_code=user[0]['Language'], email=user2[0]['email'],
                                            Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                            Text=form.cleaned_data.get('Text'), Rating=form.cleaned_data.get('Rating'), Page='Сброс пароля')
                except:
                    username = form.cleaned_data.get('TG_contact')
                    user2 = User.objects.filter(username=username).values('username', 'email')
                    user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                    FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                            Language_code=user[0]['Language'], email=user2[0]['email'],
                                            Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                            Text=form.cleaned_data.get('Text'), Rating=-1, Page='Сброс пароля')
            elif num == 3: #Ввод email для смены email
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=form.cleaned_data.get('Rating'), Page='Смена email')
            elif num == 4: #1 этап регистрации (TG_Contact, пароль)
                ExchangeName = ''
                username = form.cleaned_data.get('TG_contact')
                FeedBack.objects.create(User=username, Country_code='-',Language_code='-',Name='-',Text=form.cleaned_data.get('Text'), Rating=-1, Page='1 этап регистрации (TG_Contact, пароль)')
            elif num == 5: #2 этап регистрации (ФИО, Тип пользователя, Город, Страна)
                ExchangeName = ''
                username = request.user
                FeedBack.objects.create(User=username, Country_code='-',Language_code='-',Name='-',Text=form.cleaned_data.get('Text'), Rating=-1, Page='2 этап регистрации (ФИО, Тип пользователя, Город, Страна) ')
            elif num == 6: #Регистрация Центра прибыли и затрат
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Регистрация Центра прибыли и затрат')
            elif num == 7: #1 этап регистрации обменника (Выбор организатора)
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='1 этап регистрации обменника (Выбор организатора)')
            elif num == 8: #2 этап регистрации обменника (Страна, Город, Наименование, Тип доставки)
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='2 этап регистрации обменника (Страна, Город, Наименование, Тип доставки)')
            elif num == 9: #3 этап регистрации обменника (Регистрация сотрудника)
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='3 этап регистрации обменника (Регистрация сотрудника)')
            elif num == 10: #Настройка направлений сделок обменника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Создание новых направлений сделок в новый обменник')
            elif num == 11: #Настройка источников курсов валют (для новых направлений сделок)
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Выбор источников курсов валют для новых направлений сделок')
            elif num == 12: #Меню настройки обменников (Добавить новый, Редактирование орг. структуры обменников)
                ExchangeName = ''
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Меню настройки обменников (Добавить новый, Редактирование орг. структуры обменников)')
            elif num == 13: #Настройка орг. структуры обменника (Главное меню)
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                exch_name = str(PCCNTR_ExchP.objects.get(pk=num2).ExchangePointName)
                user_1 = Users.objects.filter(TG_Contact=username).values('Name', 'Surname')
                EPID = PCCNTR_ExchP.objects.filter(ExchangePointName=exch_name).values_list('ExchangePointID',flat=True).order_by(
                    'ExchangePointID')
                EPID_str = '; '.join(EPID)
                user_2 = Users_PCCNTR.objects.filter(TG_Contact=username, ExchangePointID=EPID_str).values('COUNTRY', 'Language', 'PCCNTR',"ExchangePointID")
                FeedBack.objects.create(User=username, Country_code=user_2[0]['COUNTRY'],
                                        Language_code=user_2[0]['Language'], email=user2[0]['email'],
                                        Name=str(user_1[0]['Surname'] + " " + user_1[0]['Name']),
                                        PCCNTR=user_2[0]['PCCNTR'],
                                        ExchangePointID=user_2[0]['ExchangePointID'],
                                        Text=form.cleaned_data.get('Text'),
                                        Rating=-1, Page='Настройка орг. структуры обменника (Главное меню)')
            elif num == 14: #Настройка орг. структуры обменника - Изменение организатора обменника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка орг. структуры обменника (Изменение организатора обменника)')
            elif num == 15: #Настройка орг. структуры обменника - Изменение основной информации обменника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка орг. структуры обменника (Изменение основной информации обменника (Страна, Город, Наименование, Тип доставки))')
            elif num == 16: #Настройка орг. структуры обменника - Управление персоналом обменника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка орг. структуры обменника (Управление персоналом обменника)')
            elif num == 17: #Настройка орг. структуры обменника - Управление персоналом обменника - Настройки сотрудника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                emp_name = Users_PCCNTR.objects.get(pk=num2).TG_Contact
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка орг. структуры обменника (Управление персоналом обменника - Настройки сотрудника)')
            elif num == 18: #Настройка орг. структуры обменника - Управление персоналом обменника - Подтверждение увольнения сотрудника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                emp_name = Users_PCCNTR.objects.get(pk=num2).TG_Contact
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка орг. структуры обменника (Управление персоналом обменника - Подтверждение увольнения сотрудника)')
            elif num == 19: #Настройка направлений сделок - Выбор обменника и направления сделок
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка направлений сделок (Выбор обменника и направления сделок)')
            elif num == 20: #Настройка направлений сделок после выбора обменника и выбора направлений сделок
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка направлений сделок (Изменение параметров направлений сделок)')
            elif num == 21: #Удаление направлений сделок - Выбор обменника и направления сделок
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Удаление направлений сделок (Выбор обменника и направления сделок)')
            elif num == 22: #Настройка источников курсов валют (для новых направлений сделок)
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Изменение источников курсов валют')
            elif num == 23: #Создание новых направлений сделок в ранее созданный обменник
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Создание новых направлений сделок в ранее созданный обменник')
            elif num == 24: #Редактирование Центра прибыли и затрат
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Редактирование Центра прибыли и затрат')   
            elif num == 25: #Редактирование персональных данных пользователя
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Редактирование персональных данных пользователя') 
            elif num == 26: #Общие настройки
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Общие настройки')    
            elif num == 27: #Покупка на P2P маркете - Главное меню
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Главное меню)')   
            elif num == 28: #Покупка на P2P маркете - Доска объявлений
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Доска объявлений)')      
            elif num == 29: #Покупка на P2P маркете - Оформление заявки на обмен
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Оформление заявки на обмен)')   
            elif num == 30: #Покупка на P2P маркете - Редактирование заявки на обмен
                order_num = num2
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Редактирование заявки на обмен)')   
            elif num == 31: #Баланс и бонусы
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Баланс и бонусы')  
            elif num == 32: #Баланс и бонусы - Пополнение баланса
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Баланс и бонусы (Пополнение баланса)')  
            elif num == 33: #Баланс и бонусы - Вывод средств
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Баланс и бонусы (Вывод средств)')  
            elif num == 34: #Безопасность
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Безопасность (смена пароля или email)')
            elif num == 35: #Выбор типа пользователя
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Выбор типа пользователя') 
            elif num == 36: #Выбор обменника
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1, 
                                        Page='Выбор обменника (для организаторов и сотрудников)') 
            elif num == 37: #Покупка на P2P маркете - Оформление предложения на обмен
                order_num = num2
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Оформление предложения на обмен)')  
            elif num == 38: #Авторизация
                ExchangeName = ''
                username = form.cleaned_data.get('TG_contact')
                FeedBack.objects.create(User=username, Country_code='-',Language_code='-',Name='-',Text=form.cleaned_data.get('Text'), 
                                        Rating=-1, Page='Авторизация')
            elif num == 39: # Раздел "Уведомления"
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Уведомления')
            elif num == 42: #Настройка скидочной программы
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Настройка скидочной программы (Изменение параметров скидочной программы)')
            elif num == 43: #Покупка на P2P маркете - Выбор предложения на обмен
                request_num = num2
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Выбор предложения на обмен)')
            elif num == 44: #Покупка на P2P маркете - Сделки
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')

                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Сделки)')
            elif num == 45: #Покупка на P2P маркете - Окно чата сделки
                deal_num = num2
                username = request.user
                user2 = User.objects.filter(username=username).values('username', 'email')
                user = Users.objects.filter(TG_Contact=username).values('Name', 'Surname', 'COUNTRY', 'Language')
                FeedBack.objects.create(User=username, Country_code=user[0]['COUNTRY'],
                                        Language_code=user[0]['Language'], email=user2[0]['email'],
                                        Name=str(user[0]['Surname'] + " " + user[0]['Name']),
                                        Text=form.cleaned_data.get('Text'), Rating=-1,
                                        Page='Покупка на P2P маркете (Окно чата сделки)')

            if num == 1:
                return redirect('home', usertype)
            elif num == 2:
                return redirect('password_reset')
            elif num == 3:
                return redirect('email_reset')
            elif num == 4:
                return redirect('register')
            elif num == 5:
                return redirect('register2')
            elif num == 6:
                return redirect('register_pccntr')
            elif num == 7:
                return redirect('general_settings_exchange_structure_new_1')
            elif num == 8:
                return redirect('general_settings_exchange_structure_new_2')
            elif num == 9:
                return redirect('general_settings_exchange_structure_new_3', num2)
            elif num == 10:
                return redirect('general_settings_exchange_deals_new')
            elif num == 11:
                return redirect('general_settings_exchange_rate_source_new')
            elif num == 12:
                return redirect('general_settings_exchange_points')
            elif num == 13:
                return redirect('general_settings_change_exchange_structure', exch_name)
            elif num == 14:
                return redirect('general_settings_change_exchange_structure_1')
            elif num == 15:
                return redirect('general_settings_change_exchange_structure_2')
            elif num == 16:
                return redirect('general_settings_change_exchange_structure_3_menu')
            elif num == 17:
                return redirect('general_settings_change_exchange_structure_3_employee', emp_name)
            elif num == 18:
                return redirect('general_settings_change_exchange_structure_3_delete_employee', emp_name)
            elif num == 19:
                return redirect('general_settings_change_exchange_deals_1')
            elif num == 20:
                return redirect('general_settings_change_exchange_deals_2')
            elif num == 21:
                return redirect('general_settings_delete_exchange_deals')
            elif num == 22:
                return redirect('general_settings_change_exchange_rate_source')
            elif num == 23:
                return redirect('general_settings_exchange_deals_add_new')
            elif num == 24:
                return redirect('general_settings_pccntr')
            elif num == 25:
                return redirect('general_settings_personal')
            elif num == 26:
                return redirect('general_settings')
            elif num == 27:
                return redirect('P2Pmarket')
            elif num == 28:
                return redirect('P2Pmarket_Bulletin_board')
            elif num == 29:
                return redirect('P2Pmarket_Exchange_order')
            elif num == 30:
                return redirect('P2Pmarket_change_Exchange_order', order_num)
            elif num == 31:
                return redirect('balance_settings')
            elif num == 32:
                return redirect('balance_settings_refill_balance')
            elif num == 33:
                return redirect('balance_settings_withdraw_funds')
            elif num == 34:
                return redirect('safety')
            elif num == 35:
                return redirect('check_usertype')
            elif num == 36:
                return redirect('choose_exchange', usertype)
            elif num == 37:
                return redirect('P2Pmarket_Exchange_request', order_num)
            elif num == 38:
                return redirect('login')
            elif num == 39:
                return redirect('Notification')
            elif num == 42:
                return redirect('general_settings_change_exchange_deals_bonus_2')
            elif num == 43:
                return redirect('P2Pmarket_Choose_Request', request_num)
            elif num == 44:
                return redirect('P2Pmarket_Deal_board')
            elif num == 45:
                return redirect('room', deal_num)
        else:
            form = Feedback(num)
    else:
        form = Feedback(num)
        if num == 13:
            exch_name = str(PCCNTR_ExchP.objects.get(pk=num2).ExchangePointName)
            emp_name = ''
            order_num = 0
            request_num = 0
            deal_num = 0
        elif num == 17 or num == 18:
            exch_name = ''
            emp_name = Users_PCCNTR.objects.get(pk=num2).TG_Contact
            order_num = 0
            request_num = 0
            deal_num = 0
        elif num == 30 or num == 37:
            exch_name = ''
            emp_name = ''
            order_num = num2
            request_num = 0
            deal_num = 0
        elif num == 43:
            exch_name = ''
            emp_name = ''
            order_num = 0
            request_num = num2
            deal_num = 0
        elif num == 45:
            exch_name = ''
            emp_name = ''
            order_num = 0
            request_num = 0
            deal_num = num2
        else:
            exch_name = ''
            emp_name = ''
            order_num = 0
            request_num = 0
            deal_num = 0
    return render(request, 'testsite/Feedback.html',
                  {'form': form, 'title': 'Обратная связь', 'usertype': usertype, 'num': num, 'num2': num2, 
                        'exch_name':exch_name, 'emp_name':emp_name, 'order_num':order_num, 'request_num':request_num,
                        'deal_num':deal_num})


class LoginUser(LoginView):
    form_class = LoginUserForm
    template_name = 'testsite/login.html'

    def get_success_url(self):
        return reverse_lazy('check_usertype')


def LogOut(request):
    cache.delete('user_type')
    cache.delete('ExchangeName')
    logout(request)
    return redirect('login')


# # если есть криптовалюта из TradingView
# def tradingview_crypto(currency_to_buy, currency_to_sell, amount, profit_norms):
#     opertype = str(currency_to_sell) + str(currency_to_buy)
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#         "Content-Length": "396",
#         "Content-Type": "text/plain;charset=UTF-8",
#         "Origin": "https://www.tradingview.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
#     }
#     data = {
#         "columns": ["currency_logoid", "base_currency_logoid", "name", "description", "update_mode", "type",
#                     "typespecs", "close"]
#         , "filter": [{"left": "exchange", "operation": "nequal", "right": "BITMEX"}
#             , {"left": "description", "operation": "nmatch", "right": "Calculated By Tradingview"}
#             , {"left": "description", "operation": "nmatch", "right": "DOLLAR FORWARD"}
#             , {"left": "name", "operation": "match", "right": opertype}]
#         , "ignore_unknown_fields": False
#         , "options": {"lang": "en"}
#         , "range": [0, 2000]
#         , "sort": {"sortBy": "24h_vol|5", "sortOrder": "desc"},
#     }
#
#     response = requests.post(url='https://scanner.tradingview.com/crypto/scan', headers=headers, json=data).json()
#     #print(response['data'][0]['d'])
#     currency_cost = response['data'][0]['d'][7]
#     currency_full_value = currency_cost * amount
#     max_percent = 0
#     for profit_norm in profit_norms:
#         if currency_full_value >= profit_norm['ExchTOAmount_Min'] and currency_full_value <= profit_norm[
#             'ExchTOAmount_Max']:
#             Norm_Prib = profit_norm['EP_PRFTNORM']
#             Norm_Prib_Name_1 = []
#             Norm_Prib_Name_2 = []
#             Norm_Prib_Percent = []
#             if ';' in Norm_Prib:
#                 while ";" in Norm_Prib:
#                     N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
#                     Name = N_P[:N_P.find(' ')].strip()
#                     Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
#                     Name_1 = Name[:Name.find("-")].strip()
#                     Norm_Prib_Name_1.append(Name_1)
#                     Name_2 = Name[Name.find("-") + 1:].strip()
#                     Norm_Prib_Name_2.append(Name_2)
#                     Norm_Prib_Percent.append(Percent)
#                     Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#             else:
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#
#             for i in range(len(Norm_Prib_Name_1)):
#                 if currency_full_value >= float(Norm_Prib_Name_1[i]) and currency_full_value <= float(
#                         Norm_Prib_Name_2[i]):
#                     if max_percent < float(Norm_Prib_Percent[i]):
#                         max_percent = float(Norm_Prib_Percent[i])
#
#     currency_value = currency_cost * (1 + float(max_percent / 100))
#     currency_full_value = round(currency_value, 5) * amount
#     results = {'currency_value': round(currency_value, 5), 'currency_full_value': round(currency_full_value, 2)}
#     return results
#
#
# # расчет для обмена обычных валют из TradingView
# def tradingview_forex(currency_to_buy, currency_to_sell, amount, profit_norms):
#     opertype = str(currency_to_sell) + str(currency_to_buy)
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7",
#         "Content-Length": "396",
#         "Content-Type": "text/plain;charset=UTF-8",
#         "Origin": "https://www.tradingview.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36"
#     }
#     data = {"columns": ["currency_logoid", "base_currency_logoid", "name", "description", "update_mode", "type",
#                         "typespecs", "close"]
#         , "filter": [{"left": "name", "operation": "match", "right": opertype}]
#         , "ignore_unknown_fields": False
#         , "options": {"lang": "en"}
#         , "range": [0, 2000]
#         , "sort": {"sortBy": "name", "sortOrder": "asc", "nullsFirst": False}
#         , "preset": "forex_rates_all"
#             }
#
#     response = requests.post(url='https://scanner.tradingview.com/forex/scan', headers=headers, json=data).json()
#     #(response['data'][0]['d'])
#     currency_cost = float(response['data'][0]['d'][7])
#     currency_full_value = currency_cost * amount
#     max_percent = 0
#     for profit_norm in profit_norms:
#         if currency_full_value >= profit_norm['ExchTOAmount_Min'] and currency_full_value <= profit_norm[
#             'ExchTOAmount_Max']:
#             Norm_Prib = profit_norm['EP_PRFTNORM']
#             Norm_Prib_Name_1 = []
#             Norm_Prib_Name_2 = []
#             Norm_Prib_Percent = []
#             if ';' in Norm_Prib:
#                 while ";" in Norm_Prib:
#                     N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
#                     Name = N_P[:N_P.find(' ')].strip()
#                     Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
#                     Name_1 = Name[:Name.find("-")].strip()
#                     Norm_Prib_Name_1.append(Name_1)
#                     Name_2 = Name[Name.find("-") + 1:].strip()
#                     Norm_Prib_Name_2.append(Name_2)
#                     Norm_Prib_Percent.append(Percent)
#                     Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#             else:
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#
#             for i in range(len(Norm_Prib_Name_1)):
#                 if currency_full_value >= float(Norm_Prib_Name_1[i]) and currency_full_value <= float(
#                         Norm_Prib_Name_2[i]):
#                     if max_percent < float(Norm_Prib_Percent[i]):
#                         max_percent = float(Norm_Prib_Percent[i])
#
#     currency_value = currency_cost * (1 + float(max_percent / 100))
#     currency_full_value = round(currency_value, 5) * amount
#     results = {'currency_value': round(currency_value, 5), 'currency_full_value': round(currency_full_value, 2)}
#     return results
#
#
# # если есть криптовалюта из Bybit
# def bybit_crypto(currency_to_buy, currency_to_sell, amount, profit_norms, bank_name):
#     headers = {
#         "Accept": "application/json",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Accept-Language": "ru-RU",
#         "Cache-Control": "no-cache",
#         "Content-Length": "149",
#         "content-type": "application/json;charset=UTF-8",
#         "Origin": "https://www.bybit.com",
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36"
#     }
#
#     if bank_name == 'Сбербанк':
#         payment = ["582"]
#     elif bank_name == 'Тинькофф':
#         payment = ["581"]
#     elif bank_name == 'Райффайзен':
#         payment = ["64"]
#
#     if bank_name == '':
#         data = {"userId": 19502056,
#                 "tokenId": currency_to_sell,
#                 "currencyId": currency_to_buy,
#                 "side": "1",
#                 "size": "10",
#                 "page": "1",
#                 "amount": "",
#                 "authMaker": False,
#                 "canTrade": False}
#     else:
#         data = {"userId": 19502056,
#                 "tokenId": currency_to_sell,
#                 "currencyId": currency_to_buy,
#                 "payment": payment,
#                 "side": "1",
#                 "size": "10",
#                 "page": "1",
#                 "amount": "",
#                 "authMaker": False,
#                 "canTrade": False}
#
#     r = requests.post('https://api2.bybit.com/fiat/otc/item/online', headers=headers, json=data)
#     json_data = r.json()
#     currency_value = 0
#     for row in json_data['result']['items']:
#         order_min = float(row['minAmount'])
#         order_max = float(row['maxAmount'])
#
#         currency_cost = float(row['price'])
#         value_need = amount * currency_cost
#
#         if value_need >= order_min and value_need <= order_max:
#             currency_value = currency_cost
#             currency_full_value = value_need
#
#     if currency_value == 0:
#         currency_cost = float(json_data['result']['items'][0]['price'])
#         currency_full_value = amount * currency_cost
#
#     max_percent = 0
#     for profit_norm in profit_norms:
#         if currency_full_value >= profit_norm['ExchTOAmount_Min'] and currency_full_value <= profit_norm[
#             'ExchTOAmount_Max']:
#             Norm_Prib = profit_norm['EP_PRFTNORM']
#             Norm_Prib_Name_1 = []
#             Norm_Prib_Name_2 = []
#             Norm_Prib_Percent = []
#             if ';' in Norm_Prib:
#                 while ";" in Norm_Prib:
#                     N_P = Norm_Prib[:Norm_Prib.find(";")].strip()
#                     Name = N_P[:N_P.find(' ')].strip()
#                     Percent = N_P[N_P.find(':') + 2:N_P.find('%')].strip()
#                     Name_1 = Name[:Name.find("-")].strip()
#                     Norm_Prib_Name_1.append(Name_1)
#                     Name_2 = Name[Name.find("-") + 1:].strip()
#                     Norm_Prib_Name_2.append(Name_2)
#                     Norm_Prib_Percent.append(Percent)
#                     Norm_Prib = Norm_Prib[Norm_Prib.find(";") + 1:].strip()
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#             else:
#                 Name = Norm_Prib[:Norm_Prib.find(' ')].strip()
#                 Percent = Norm_Prib[Norm_Prib.find(':') + 2:Norm_Prib.find('%')].strip()
#                 Name_1 = Name[:Name.find("-")].strip()
#                 Norm_Prib_Name_1.append(Name_1)
#                 Name_2 = Name[Name.find("-") + 1:].strip()
#                 Norm_Prib_Name_2.append(Name_2)
#                 Norm_Prib_Percent.append(Percent)
#
#             for i in range(len(Norm_Prib_Name_1)):
#                 if currency_full_value >= float(Norm_Prib_Name_1[i]) and currency_full_value <= float(
#                         Norm_Prib_Name_2[i]):
#                     if max_percent < float(Norm_Prib_Percent[i]):
#                         max_percent = float(Norm_Prib_Percent[i])
#
#     currency_value = currency_cost * (1 + float(max_percent / 100))
#     currency_full_value = round(currency_value, 5) * amount
#
#     results = {'currency_value': round(currency_value, 5), 'currency_full_value': round(currency_full_value, 2)}
#     return results