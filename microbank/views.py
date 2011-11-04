
from deform import Button
from deform import Form
from deform import ValidationFailure
from deform.widget import TextInputWidget
from microbank.models import DBSession
from microbank.models import InstanceConfig
from microbank.models import MicroBankRoot
from microbank.models import User
from pyramid.encode import urlencode
from pyramid.url import resource_url
from pyramid.view import view_config
from urllib2 import HTTPError
from webob.exc import HTTPFound
import colander
import json
import requests
import time


request_scope = 'offline view_wallet'


def get_instance_config():
    dbsession = DBSession()
    rows = dbsession.query(InstanceConfig.name, InstanceConfig.value).all()
    data = dict(rows)
    if 'client_id' not in data or 'client_secret' not in data:
        raise ValueError('This instance has not yet been configured.')
    return data


class ConfigureSchema(colander.MappingSchema):
    # The client_id is always an integer. It may be larger than 32 bits.
    client_id = colander.SchemaNode(
        colander.Integer(), validator=colander.Range(min=1),
        widget=TextInputWidget(size=15))
    # The client_secret is always base 64 encoded.
    client_secret = colander.SchemaNode(
        colander.String(), validator=colander.Regex(r'[A-Za-z0-9_\-]+$'),
        widget=TextInputWidget(size=40))
    authorize_url = colander.SchemaNode(
        colander.String(), title='Authorize URL',
        widget=TextInputWidget(size=40))
    api_url = colander.SchemaNode(
        colander.String(), title='API URL',
        widget=TextInputWidget(size=40))


@view_config(context=MicroBankRoot, renderer='templates/root.pt')
def root_view(root, request):
    return {'users': list(root)}


@view_config(name='configure', context=MicroBankRoot,
    renderer='templates/configure.pt')
def configure_view(root, request):
    form = Form(ConfigureSchema(),
        buttons=(Button(name='submit', value='Save Changes'),))
    message = ''
    dbsession = DBSession()

    if 'submit' in request.POST:
        try:
            data = form.validate(request.POST.items())
        except ValidationFailure, e:
            rform = e.render()
        else:
            for old_obj in dbsession.query(InstanceConfig).filter(
                    InstanceConfig.name.in_(data.keys())).all():
                dbsession.delete(old_obj)
            for name, value in data.items():
                dbsession.add(InstanceConfig(name=name, value=value))
            rform = form.render(data)
            message = 'Changes Saved.'
    else:
        data = {
            # Provide some default values.
            'authorize_url': 'https://wingcash.com/authorize',
            'api_url': 'https://api1.wingcash.com',
        }
        rows = dbsession.query(InstanceConfig.name, InstanceConfig.value).all()
        data.update(dict(rows))
        rform = form.render(data)

    return {'rform': rform, 'message': message}


@view_config(name='login', context=MicroBankRoot)
def login(root, request):
    """User started the login process.

    Redirect to the authorize endpoint, where the user will enter
    credentials, then WingCash will redirect the browser to login_callback.
    """
    instance_config = get_instance_config()
    redirect_uri = resource_url(root, request, 'login_callback')
    # See the OAuth 2 spec, section 4.1.1
    q = urlencode([
        ('response_type', 'code'),
        ('client_id', instance_config['client_id']),
        ('redirect_uri', redirect_uri),
        ('scope', request_scope),
        ('state', 'abc123'),
    ])
    url = '%s?%s' % (instance_config['authorize_url'], q)
    return HTTPFound(location=url)


@view_config(name='login_callback', context=MicroBankRoot,
    renderer='templates/login_error.pt')
def login_callback(root, request):
    """The user authenticated with WingCash.

    Turn the received authorization code into an access token,
    get the user info, and add the user to our database.
    Finally, redirect to the user's new page.
    """
    instance_config = get_instance_config()

    # First check for errors sent by the auth server.

    # See the OAuth 2 spec, section 4.1.2
    if request.params.get('state') != 'abc123':
        # Shield against a CSRF attempt.
        return {'error': 'login_callback did not receive correct state value'}

    if 'error' in request.params:
        return {'error': 'OAuth Error: %s (%s)' % (request.params['error'],
            request.params.get('error_description', 'no description'))}

    # We have an authorization code.  Use it to get an access token.

    code = request.params['code']
    redirect_uri = resource_url(root, request, 'login_callback')
    # See the OAuth 2 spec, sections 4.1.3 and 2.3.1
    token_response = requests.post(instance_config['api_url'] + '/token', {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': redirect_uri,
        'client_id': instance_config['client_id'],
        'client_secret': instance_config['client_secret'],
    })
    try:
        token_response.raise_for_status()
    except HTTPError:
        ct = token_response.headers.get('content-type', '')
        if ct.startswith('application/json'):
            token_data = json.loads(token_response.content)
            if 'error' in token_data:
                # See the OAuth 2 spec, section 5.2
                return {
                    'error': 'OAuth Error: %s (%s)' % (token_data['error'],
                        token_data.get('error_description', 'no description')),
                }
        raise

    # We have an access token.  Use it to get info about the user who
    # logged in.

    # See the OAuth 2 spec, section 5.2
    token_data = json.loads(token_response.content)
    access_token = token_data['access_token']
    token_type = token_data['token_type']
    if token_type.lower() != 'bearer':
        return {
            'error': 'Received an unsupported token type: %s' % token_type,
        }
    user = prepare_user(access_token, root)

    # Redirect to the user object.
    url = resource_url(user, request)
    return HTTPFound(location=url)


def prepare_user(access_token, parent):
    """Create or update a User object using the given access token."""
    instance_config = get_instance_config()
    me_response = requests.post(instance_config['api_url'] + '/me', {
        'access_token': access_token,
    })
    me_response.raise_for_status()

    me = json.loads(me_response.content)
    wingcash_id = me['id']
    dbsession = DBSession()
    user = dbsession.query(User).get(wingcash_id)
    if user is None:
        user = User(wingcash_id=wingcash_id)
        dbsession.add(user)
    user.__parent__ = parent
    user.__name__ = unicode(wingcash_id)
    user.access_token = access_token
    user.display_name = unicode(me['display_name'])
    user.url = me['url']
    user.photo50 = me['photo50']
    user.cash_usd = me['cash_usd']
    return user


@view_config(context=User, renderer='templates/user.pt')
def view_user(user, request):
    update_url = resource_url(
        user, request, 'update', query={'_': str(time.time())})
    return {'user': user, 'update_url': update_url}


@view_config(name='update', context=User)
def update_user(user, request):
    parent = user.__parent__
    user2 = prepare_user(user.access_token, parent)
    url = resource_url(user2, request)
    return HTTPFound(location=url)
