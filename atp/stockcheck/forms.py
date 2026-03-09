from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from stockcheck.models import Profile

class ProductForm(forms.Form):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(ProductForm, self).__init__(*args, **kwargs)
        self.fields['plant_option'].queryset = User.objects.filter(username=user.username)[0].plant.all().exclude(description__isnull=True)

    attr_choices = (
    ('attr', 'Choose a search option..'),
    ('Arc', 'Arc SKU'),
    ('Old', 'Vendor SKU'),
    #('Ptn', 'Pattern'),
    #('Unv', 'Universe'),
    )
    #plant_choices = (
    #('Plant', 'Choose a plant..'),
    #('9993', 'ACME Corp'),
    #('9994', 'Arc Millville'),
    #('9943', 'Arc Canada'),
    #)
    attr_type = forms.ChoiceField(choices= attr_choices, required=True, widget=forms.Select(attrs={'class': 'form-control mx-sm-3','id': 'attr_type', 'aria-describedby': 'attrHelpBlock'}), label="")
    plant_option = forms.ModelChoiceField(queryset=None,empty_label='Select a plant',required=True,widget=forms.Select(attrs={'class': 'form-control mx-sm-3', 'id': 'plant_option','aria-describedby': 'plantHelpBlock'}), label="" )
    product_number = forms.CharField(widget=forms.Textarea(attrs={'class': 'form-control', 'style': 'width:450px;', 'rows': '2', 'id': 'product_id','aria-describedby': 'productHelpBlock',}),label="")


class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Last name'}))
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.',widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}))
    username = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Username'}))
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'email', 'password1','password2' )

"""
class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'First name'}))
    last_name = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Last name'}))
    email = forms.EmailField(max_length=254, required=True, help_text='Required. Inform a valid email address.',widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Email address'}))
    password1 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter your password'}))
    password2 = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'}))

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2',)

"""
class ProfileForm(forms.ModelForm):
    BUSINESS_CHOICES = (
    (' ','Select the business entity that you work with'),
    ('AINA', 'ACME International North America'),
    ('Brand_D', 'Brand_D International')
    )
    company = forms.CharField(max_length=30, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Company name'}))
    role = forms.CharField(max_length=75, required=True, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Role / Title'}))
    website = forms.URLField(max_length=75, required=False, help_text='Required',widget=forms.TextInput(attrs={'class': 'form-control','placeholder': 'Website'}))
    business = forms.ChoiceField(required=True,choices=BUSINESS_CHOICES, widget=forms.Select(attrs={'class':'form-control','id': 'business_org'}))
    
    class Meta:
        model = Profile
        fields = ('company', 'role', 'website', 'business')

