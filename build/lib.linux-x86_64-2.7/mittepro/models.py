# -*- coding: utf-8 -*-
import re
import base64
from datetime import datetime
from mittepro.exceptions import InvalidParam
from mittepro import item_in_dict, item_not_in_dict, attr_in_instance, attr_not_in_instance


class Mail(object):
    TRACK_EMAIL_REGEX = re.compile(r"<.*?(.*).*>")
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9.!#$%&’*+/=?^_`{|}~-]+@[a-zA-Z0-9-]+(?:\.[a-zA-Z0-9-]+)*$")

    def __init__(self, **kwargs):
        assert 'from_email' in kwargs or item_in_dict(kwargs, 'use_tpl_default_email'), \
            'Forneça o email do remetente'
        assert 'recipient_list' in kwargs and len(kwargs.get('recipient_list')), \
            'Impossível enviar um email sem uma lista de destinatários'
        assert 'subject' in kwargs or item_in_dict(kwargs, 'use_tpl_default_subject'), \
            'Impossível enviar um email sem um assunto'
        self.attach_size_limit_mb = 10
        self.attach_size_limit_b = self.attach_size_limit_mb * 1024 * 1024

        # General mail vars
        self.set_attr('tags', kwargs)
        self.set_attr('send_at', kwargs)
        self.validate_send_at(kwargs)
        self.set_attr('subject', kwargs)
        self.set_attr('from_name', kwargs)
        self.set_attr('from_email', kwargs)
        self.set_attr('message_text', kwargs)
        self.set_attr('message_html', kwargs)
        self.set_attr('recipient_list', kwargs)
        self.check_recipient_list()
        self.set_attr('activate_tracking', kwargs)
        self.set_attr('track_open', kwargs)
        self.set_attr('track_html_link', kwargs)
        self.set_attr('track_text_link', kwargs)
        self.set_attr('get_text_from_html', kwargs)
        self.set_attr('attachments', kwargs)
        self.check_attachments()
        # self.set_attr('expose_recipients_list', kwargs)

        # Template mail vars
        self.set_attr('headers', kwargs)
        self.set_attr('context', kwargs)
        self.set_attr('template_slug', kwargs)
        self.set_attr('use_tpl_default_name', kwargs)
        self.set_attr('use_tpl_default_email', kwargs)
        self.set_attr('use_tpl_default_subject', kwargs)
        self.set_attr('context_per_recipient', kwargs)

    def validate_send_at(self, kwargs):
        send_at = kwargs.get('send_at')
        if not send_at:
            return True
        try:
            datetime.strptime(send_at, '%Y-%m-%d %H:%M:%S')
            return True
        except ValueError:
            raise InvalidParam(message_values=("'send_at'", 'Invalid format, expecting: YYYY-mm-dd HH:MM:SS'))

    def set_attr(self, attr, kwargs):
        if attr in kwargs:
            setattr(self, attr, kwargs.get(attr))

    def __track_email(self, value):
        tracked = self.TRACK_EMAIL_REGEX.search(value)
        if tracked:
            return tracked.group(1)
        return None

    def __validate_email(self, email):
        valid = self.EMAIL_REGEX.match(email)
        return valid is not None

    def __validate_recipient(self, value):
        email = self.__track_email(value)
        return email and self.__validate_email(email)

    def check_recipient_list(self):
        exception_reason = "O formato esperado ('nome <email>'; ou '<email>') não foi encontrado"
        for recipient in getattr(self, 'recipient_list'):
            if not self.__validate_recipient(recipient):
                raise InvalidParam(message_values=("'recipient_list'", exception_reason))

    def check_attachment_size(self, file_size, attach_name=None):
        if file_size >= self.attach_size_limit_b:
            diff = file_size - self.attach_size_limit_b
            diff = '%.2f' % (diff / float(1000 * 1000))
            if attach_name:
                message = """The size of one of the attachments exceeds the limit of {0} MB allowed.
                The attachment '{1}' exceeds in {2} MB""".format(
                    self.attach_size_limit_mb, attach_name, diff)
            else:
                message = """The sum of the size of the attachments exceeds the {0} MB allowed.
                The total exceeds in {1} MB""".format(self.attach_size_limit_mb, diff)
            raise InvalidParam(message_values=("'attachments'", message))

    def check_attachments(self):
        if not isinstance(getattr(self, 'attachments'), list):
            raise InvalidParam(
                message_values=(
                    "'attachments'",
                    "Attachments should be a List of dictionaries. Like: [{name: 'foo.bar', file: 'bWl0dGVwcm8=\n'}]"
                ))
        total_attachs_size = 0
        for attach in getattr(self, 'attachments'):
            if not isinstance(attach, dict):
                raise InvalidParam(
                    message_values=(
                        "'attachments'",
                        "Attachments should be a List of dictionaries. "
                        "Like: [{name: 'foo.bar', file: 'bWl0dGVwcm8=\n'}]"
                    ))
            if 'name' not in attach:
                raise InvalidParam(
                    message_values=(
                        "'attachments'",
                        "Attachment should have an name. Like: {name: 'foo.bar', file: 'bWl0dGVwcm8=\n'}"
                    ))
            if 'file' not in attach:
                raise InvalidParam(
                    message_values=(
                        "'attachments'",
                        "Attachment should have the contents of the file in base64. "
                        "Like: {name: 'foo.bar', file: 'bWl0dGVwcm8=\n'}"
                    ))
            try:
                dfile = base64.decodestring(attach['file'])
            except TypeError:
                raise InvalidParam(message_values=("'attachments'", 'Attachment file should be in base64.'))
            file_size = len(dfile)
            self.check_attachment_size(file_size, attach['name'])
            total_attachs_size += file_size
        self.check_attachment_size(total_attachs_size)

    @staticmethod
    def __mount_param_from(payload):
        payload['from'] = ''
        if 'from_name' in payload and payload['from_name']:
            payload['from'] += payload['from_name']
            del payload['from_name']
        if 'from_email' in payload and payload['from_email']:
            payload['from'] += ' <{0}>'.format(payload['from_email'])
            del payload['from_email']
        return payload['from'].strip()

    def get_payload(self, endpoint='text'):
        if endpoint == 'template':
            if attr_not_in_instance(self, 'template_slug') and attr_not_in_instance(self, 'message_html'):
                raise AssertionError("Impossível enviar um email com template sem o conteúdo html. Ou você fornece "
                                     "o 'template_slug' ou o 'message_html'")
            if ((attr_in_instance(self, 'use_tpl_default_subject') or
                 attr_in_instance(self, 'use_tpl_default_email') or
                 attr_in_instance(self, 'use_tpl_default_name')) and
                    (attr_not_in_instance(self, 'template_slug'))):
                raise AssertionError("Impossível usar os recursos de um template, sem fornecer o 'template_slug'")

        payload = self.__dict__
        payload['from'] = Mail.__mount_param_from(payload)
        payload['sended_by'] = 4

        return payload


class SearchMailArgs(object):
    def __init__(self, **kwargs):
        if item_not_in_dict(kwargs, 'app_ids'):
            raise AssertionError("Parâmetro 'app_ids' não foi fornecido.")
        if item_not_in_dict(kwargs, 'start'):
            raise AssertionError("Parâmetro 'start' não foi fornecido.")
        if item_not_in_dict(kwargs, 'end'):
            raise AssertionError("Parâmetro 'start' não foi fornecido.")

        self.set_attr('end', kwargs)
        self.set_attr('start', kwargs)
        self.set_attr('status', kwargs)
        self.set_attr('appIds', kwargs)
        self.set_attr('nameSender', kwargs)
        self.set_attr('emailSender', kwargs)
        self.set_attr('templateSlug', kwargs)
        self.set_attr('nameReceiver', kwargs)
        self.set_attr('emailReceiver', kwargs)

    def set_attr(self, attr, kwargs):
        if attr in kwargs:
            setattr(self, attr, kwargs.get(attr))

    def get_payload(self):
        return self.__dict__
