
from django.shortcuts import render, redirect, get_object_or_404
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
# Create your views here.
import datetime, os,json,decimal, pprint, requests, csv, xlwt, logging
import numpy as np
from django.core.cache import cache
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from datetime import date
from configparser import ConfigParser
from io import BytesIO
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
#from atp.tasks import send_email_task
from django.contrib.auth import authenticate, login
from django.conf import settings
from django.views.decorators.cache import cache_page
from xlsxwriter import Workbook
from django.http import HttpResponse, HttpResponseRedirect
from django.views.generic import View, TemplateView, ListView, FormView
from django.contrib.auth.decorators import permission_required
from stockcheck.forms import ProductForm
from pyrfc import Connection
from stockcheck.models import SearchHistory
from .forms import SignUpForm, ProfileForm
from django.core.mail import send_mail, BadHeaderError, EmailMessage, EmailMultiAlternatives
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
# from atp.tokens import account_activation_token
from django.urls import reverse
from collections import defaultdict
from atp.settings import PROJECT_DIR


CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

class MyJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            # Convert decimal instances to strings.
            return str(obj)
        return super(MyJSONEncoder, self).default(obj)

config = ConfigParser()
config.read(os.path.join(PROJECT_DIR, 'settings.ini'))

# Security patch: Use environment variables if available, fallback to settings.ini
def get_secure_connection_params():
    """Get SAP connection parameters securely from environment or settings.ini"""
    # Check for environment variables first (most secure)
    env_params = {
        'ashost': os.environ.get('SAP_HOST'),
        'sysnr': os.environ.get('SAP_SYSNR'),
        'client': os.environ.get('SAP_CLIENT'),
        'user': os.environ.get('SAP_USER'),
        'passwd': os.environ.get('SAP_PASSWORD'),
        'lang': os.environ.get('SAP_LANG', 'EN')
    }

    # If all required params are in environment, use them
    if all(v is not None for k, v in env_params.items() if k != 'lang'):
        return env_params

    # Otherwise, fallback to settings.ini for backward compatibility
    if 'connection' in config._sections:
        return dict(config._sections['connection'])

    raise ValueError("SAP connection parameters not found in environment or settings.ini")

params_connection = get_secure_connection_params()

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Create handlers
file_handler = logging.FileHandler('/var/log/gunicorn/sap_interactions.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)



"""Function to return list of products"""

def product_details(reftype, value):
    logger.info(f"SAP Call - Z_PATTERN_PRODUCTS - Input: reftype={reftype}, value={value}")
    result_array = np.array([2500,0])
    try:
        with Connection(**params_connection) as conn:
            if reftype == 'P':
                result = conn.call('Z_PATTERN_PRODUCTS', PATTERN=value)
            else:
                result = conn.call('Z_PATTERN_PRODUCTS', UNIVERSE=value)
            logger.info(f"SAP Response - Z_PATTERN_PRODUCTS - Success - Products count: {len(result['ET_MAT_DETAILS'])}")
            logger.debug(f"SAP Response Details: {json.dumps(result['ET_MAT_DETAILS'], cls=MyJSONEncoder)}")
            r = json.dumps(result['ET_MAT_DETAILS'], cls=MyJSONEncoder, indent=4, sort_keys=True)
            r=json.loads(r)
            for material in result['ET_MAT_DETAILS']:
                out_material=material['MATNR']
                result_array = np.append(result_array,out_material)
    except Exception as e:
        logger.error(f"SAP Call Failed - Z_PATTERN_PRODUCTS - Error: {str(e)}")
        raise
    return result_array

"""Function to return product information for one product"""

def stock_info(plant, product, mode):
    logger.info(f"SAP Call - Z_GET_MATERIAL_DETAILS - Input: plant={plant}, product={product}, mode={mode}")
    try:
        # Use new connector with timeout
        from stockcheck.sap_connector import get_sap_connector
        connector = get_sap_connector(timeout=30)  # 30 second timeout

        result = connector.get_material_details(plant, product, mode)

        # Check if we got an error response
        if 'error' in result:
            logger.warning(f"SAP connection issue for product {product}: {result['error']}")
            # Return the error response (it has basic structure for graceful handling)
            return result

        r = json.dumps(result, cls=MyJSONEncoder, indent=4, sort_keys=True)
        r=json.loads(r)
        return r
    except Exception as e:
        logger.error(f"SAP Call Failed - Z_GET_MATERIAL_DETAILS - Error: {str(e)}")
        # Return error response instead of raising
        return {
            'error': str(e),
            'MATNR': product,
            'WERKS': plant,
            'STOCK': 'N/A',
            'MAKTX': 'Connection Error'
        }


def product_info(plant, product):
    logger.info(f"SAP Call - BAPI_MATERIAL_GET_ALL - Input: plant={plant}, product={product}")
    try:
        # Use new connector with timeout
        from stockcheck.sap_connector import get_sap_connector
        connector = get_sap_connector(timeout=30)  # 30 second timeout

        result = connector.get_material_all(plant, product)

        # Check if we got an error response
        if 'error' in result:
            logger.warning(f"SAP connection issue for product {product}: {result['error']}")
            # Return the error response
            return result

        logger.debug(f"SAP Response - BAPI_MATERIAL_GET_ALL - Success - Product: {product}")
        r = json.dumps(result, cls=MyJSONEncoder, indent=4, sort_keys=True)
        r=json.loads(r)
        return r
    except Exception as e:
        logger.error(f"SAP Call Failed - BAPI_MATERIAL_GET_ALL - Error: {str(e)}")
        # Return error response instead of raising
        return {
            'error': str(e),
            'MATNR': product,
            'PLANT': plant,
            'MAKTX': 'Connection Error'
        }
    # Create your views here.

class IndexView(TemplateView):
    template_name = 'stockcheck/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['injected1'] = 'First text'
        context['injected2'] = 'Second text'
        return context


class AboutView(TemplateView):
    template_name = 'stockcheck/about.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aboutme'] = 'About me text'
        return context

class FeedbackView(LoginRequiredMixin,TemplateView):
    template_name = 'registration/feedback.html'
    login_url = '/login/'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['feedback'] = 'Feedback'
        return context

class ThankView(TemplateView):
    template_name = 'registration/thanks.html'

class HelpView(TemplateView):
    template_name = 'stockcheck/help.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['helpme'] = 'About me text'
        return context


class HomeView(TemplateView):
    template_name = 'stockcheck/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['helpme'] = 'About me text'
        return context
        
class SearchView(LoginRequiredMixin, FormView):
    login_url = '/login/'
    redirect_field_name = 'product/detail/'
    template_name = 'stockcheck/search.html'
    form_class = ProductForm
    success_url = 'product/detail/'

    def get_context_data(self, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        user = self.request.user
        return context

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form, **kwargs)
        else:
            return self.form_invalid(form, **kwargs)

    def get_form_kwargs(self):
        kwargs = super(SearchView, self).get_form_kwargs()
        kwargs.update({'user': self.request.user})
        return kwargs


    def form_valid(self, form, **kwargs):
        context = super(SearchView, self).get_context_data(**kwargs)
        context['form'] = form
        refnumber = form.cleaned_data['product_number'].replace(" ", "")
        plantcode = form.cleaned_data['plant_option'].code
        attrtype = form.cleaned_data['attr_type']

        logger.info(f"Search initiated - User: {self.request.user.username}, Plant: {plantcode}, Type: {attrtype}")

        def chunks(l,n):
            for i in range(0,len(l),n):
                yield l[i:i+n]

        #pattern_option = form.cleaned_data['pattern_options']
        if "," in refnumber:
            ref_numbers = refnumber.split(",")
        else:
            ref_numbers = refnumber.split()

        ref_numbers = list(chunks(ref_numbers,100))
        logger.info(f"Processing {len(ref_numbers)} chunks of reference numbers")
        try:
            if attrtype == "Arc":
                data_list = [stock_info(plantcode,product.upper(), 'M') for group in ref_numbers for product in group]

            elif attrtype =="Old":
                data_list = [stock_info(plantcode,product.upper(), 'O') for group in ref_numbers for product in group]

            #elif attrtype == "Ptn":
                #print(type(product_details()))
                #print(product_details())
            #elif attrtype == "Unv":
            if (data_list):
                logger.info(f"Successfully retrieved data for {len(data_list)} products")
                for item in data_list:
                    item['ACTUAL'] = float(item['ACTUAL'])
                    if item['EEIND']:
                        item['EEIND'] =  datetime.datetime.strptime(item['EEIND'], '%Y%m%d').strftime('%m/%d/%Y')
                    if item['DISMM'] == 'V2' or item['DISMM'] == 'V1' or item['DISMM'] == 'Z5' or item['DISMM'] == 'Z9':
                        item['DISMM'] = "Stock item"
                    elif item['DISMM'] == 'ZD' and item['PRMOD'] == '0':
                        item['DISMM'] = "On demand"
                    elif item['DISMM'] == 'ZD' and item['PRMOD'] != '0':
                        item['DISMM'] = "Stock item"
                    else:
                        item['DISMM'] = "No planning"

                context['data_list'] = data_list

                context['plant_code'] = plantcode
                d = defaultdict(dict)
                # for l in (data_list, product_list):
                #     for elem in l:
                #         d[elem['MATNR']].update(elem)
                # output_list = sorted(d.values(), key=itemgetter("MATNR"))
                #context['output_list'] = output_list
                if (len(data_list) == 1):
                    if attrtype == "Arc":
                        context['matnr'] = refnumber
                    else:
                        context['matnr'] = data_list[0]['MATNR']
                else:
                    context['list_size'] = len(data_list)
                self.request.session['data'] = data_list
                username = self.request.user.username
                history = SearchHistory()
                history.username = self.request.user
                history.time = date.today()
                history.referencekey = refnumber

                history.save()
                logger.info(f"Search history saved for user: {self.request.user.username}")
        except Exception as e:
            logger.error(f"Error processing search - User: {self.request.user.username}, Error: {str(e)}")
            raise
        return render(self.request, 'stockcheck/details.html', context)
       	

@cache_page(CACHE_TTL)
@login_required
def download_data(request):

    csvresult = request.session.get('data')
    xlsfile = BytesIO()

    if request.user.is_authenticated:

        username = request.user
        email_flag = request.POST.get("email")
        download_flag = request.POST.get("download")

        response = HttpResponse(content_type='application/ms-excel')
        filename = "Product stock info - " + username.username + " - " + str(date.today()) + ".xls"
        response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Stock Info')
        #Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = ['Product', 'Vendor SKU', 'Description','Brand','Origin','Stock (Pcs)','Stock(Including orders)(Pcs)','Next Delivery', 'Next Delivery Quantity',' Total quantity in transit', 'Supplier Open Quantity', 'Type', 'Case Pack', 'UPC/EAN', 'Case Pack Weight']

        for col_num in range(len(columns)):
            ws.write(row_num,col_num,columns[col_num],font_style)

        #Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        for item in csvresult:
            row_num +=1
            row = [
                item['MATNR'],
                item['BISMT'],
                item['MAKTX'],
                item['ZBRDES'],
                item['HERKL'],
                item['STOCK'],
                item['ACTUAL'],
                item['EEIND'],
                item['MNG01'],
                item['ZMENG'],
                item['ZKWMENG'],
                item['DISMM'],
                item['UMREZ'],
                item['EAN11'],
                item['BRGEW']
            ]
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)

        wb.save(response)
        wb.save(xlsfile)

        if download_flag:
            return response
        elif email_flag:
            subject = "Product stock info generated for - " + username.username + " on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = '<h4> This email is autogenerated and contains product availability information.</h4>'
            text_content = 'Some sample text'
            mail_content = xlsfile.getvalue()
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = []
            to_email.append(username.email)
            message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            message.attach('{}'.format(filename), mail_content, 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
            message.attach_alternative(html_content, "text/html")
            message.send()
            """send_email_task.delay(subject, text_content, from_email, to_email, mail_content, filename)"""
            return redirect('product_details')

def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('home')
    else:
        return render(request, 'account_activation_invalid.html')

class ActivationView(TemplateView):
    template_name = 'stockcheck/account_activation_sent.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['aboutme'] = 'About me text'
        return context


def signup(request):
    if request.method == 'POST':
        user_form = SignUpForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.is_active = False
            new_user.save()
            profile_user = profile_form.save(commit=False)
            if profile_user.user_id is None:
                profile_user.user_id = new_user.id
            profile_user.save()
            username = user_form.cleaned_data.get('username')
            raw_password = user_form.cleaned_data.get('password1')
            business = profile_form.cleaned_data.get('business')
            company = profile_form.cleaned_data.get('company')
            user = authenticate(username=username, password=raw_password)
            subject = "New user registration for - " + business + " for user  " + username + " on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = f'''
            <h4> This email is autogenerated. Please approve the new user signup for the product availability app.<br><hr></h4>
            <h5>Username: {username}</h5>
            <h5>Company: {company}</h5>
            <h5>Business Entity: {business}</h5>'''
            text_content = 'Some sample text'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [settings.DEFAULT_FROM_EMAIL]
            message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            message.attach_alternative(html_content, "text/html")
            message.send()
            """send_email_task.delay(subject, text_content, from_email, to_email, mail_content, filename)"""
            #login(request, user)
            return redirect(reverse('thanks'))
    else:
        user_form = SignUpForm()
        profile_form = ProfileForm()
    return render(request, 'registration/signup.html', {'user_form': user_form, 'profile_form': profile_form})

"""
def signup(request):
    if request.method == 'POST':
        user_form = SignUpForm(request.POST)
        profile_form = ProfileForm(request.POST)
        if user_form.is_valid() and profile_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.username = new_user.email  # use email as username
            new_user.is_active = False
            new_user.save()
            profile_user = profile_form.save(commit=False)
            if profile_user.user_id is None:
                profile_user.user_id = new_user.id
            profile_user.save()
            email = user_form.cleaned_data.get('email')
            raw_password = user_form.cleaned_data.get('password1')
            business = profile_form.cleaned_data.get('business')
            company = profile_form.cleaned_data.get('company')
            user = authenticate(email=email, password=raw_password)  # authenticate with email
            subject = "New user registration for - " + business + " for user  " + email + " on " + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            html_content = f'''
            <h4> This email is autogenerated. Please approve the new user signup for the product availability app.<br><hr></h4>
            <h5>Email: {email}</h5>
            <h5>Company: {company}</h5>
            <h5>Business Entity: {business}</h5>'''
            text_content = 'Some sample text'
            from_email = settings.DEFAULT_FROM_EMAIL
            to_email = [settings.DEFAULT_FROM_EMAIL]
            message = EmailMultiAlternatives(subject, text_content, from_email, to_email)
            message.attach_alternative(html_content, "text/html")
            message.send()
            send_email_task.delay(subject, text_content, from_email, to_email, mail_content, filename)
            #login(request, user)
            return redirect(reverse('thanks'))
    else:
        user_form = SignUpForm()
        profile_form = ProfileForm()
    return render(request, 'registration/signup.html', {'user_form': user_form, 'profile_form': profile_form})
"""