import sys
import hashlib
import random
import traceback
from datetime import datetime, timedelta, date

from django.test import SimpleTestCase
from django.conf import settings

from suds.client import Client

from nadine.utils import mailgun

class MailgunTestCase(SimpleTestCase):
    bob_email = "bob@bob.net"
    bob = "Bob Smith <%s>" % bob_email
    alice_email = "alice@312main.ca"
    alice = "Alice Smith <%s>" % alice_email
    frank_email = "frank@example.com"
    frank = "Frank Smith <%s>" % frank_email
    mailgun_data = {'from':bob,
        'subject': "This is a test",
        'to':[alice, frank, bob],
        'cc':[frank, alice, bob],
        'bcc':[bob, alice, frank],
    }

    def test_address_map(self):
        addresses = mailgun.address_map(self.mailgun_data, 'BUNK', [])
        self.assertEqual(addresses, {})

        exclude = []
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 3)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)
        self.assertEqual(self.bob_email, list(addresses.keys())[2], exclude)

        exclude = [self.bob_email]
        addresses = mailgun.address_map(self.mailgun_data, 'to', exclude)
        self.assertEqual(len(addresses), 2)
        self.assertEqual(self.alice_email, list(addresses.keys())[0], exclude)

    def test_clean_mailgun_data(self):
        clean_data = mailgun.clean_mailgun_data(self.mailgun_data)
        # print(clean_data)
        tos = clean_data['to']
        self.assertEqual(len(tos), 1)
        self.assertEqual(tos[0], self.alice)
        ccs = clean_data['cc']
        self.assertEqual(len(ccs), 0)
        bccs = clean_data['bcc']
        self.assertEqual(len(bccs), 1)
        self.assertEqual(bccs[0], self.frank)


class UsaepayTestCase(SimpleTestCase):
    _client = None
    _token = None

    def get_client(self):
        if not self._client:
            url = settings.USA_EPAY_SOAP_1_4
            self._client = Client(url)
        return self._client

    def get_token(self, key, pin):
        if not self._token:
            # Hash our pin
            random.seed(datetime.now())
            salt = random.randint(0, sys.maxsize)
            salted_value = "%s%s%s" % (key, salt, pin)
            pin_hash = hashlib.sha1(salted_value.encode('utf-8'))

            client = self.get_client()
            self._token = client.factory.create('ueSecurityToken')
            self._token.SourceKey = key
            self._token.PinHash.Type = 'sha1'
            self._token.PinHash.Seed = salt
            self._token.PinHash.HashValue = pin_hash.hexdigest()
        return self._token

    def test_soap(self):
        if not hasattr(settings, 'USA_EPAY_SOAP_KEY'):
            return

        key = settings.USA_EPAY_SOAP_KEY
        pin = settings.USA_EPAY_SOAP_PIN

        client = self.get_client()
        token = self.get_token(key, pin)
        # TODO - This should not be hardcoded
        username = "jacob"
        cust_num = client.service.searchCustomerID(token, username);

        self.assertTrue(cust_num != None)
