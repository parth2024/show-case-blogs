from django import forms
from django_ckeditor_5.widgets import CKEditor5Widget
from .models import Article, Category, Admin


class ArticleForm(forms.ModelForm):
    """Form for creating and editing articles"""
    
    content = forms.CharField(widget=CKEditor5Widget(config_name='extends'), required=True)
    
    class Meta:
        model = Article
        fields = ['title', 'summary', 'content', 'status', 'is_featured', 'categories']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Enter article title...'
            }),
            'summary': forms.Textarea(attrs={
                'class': 'input',
                'rows': 3,
                'placeholder': 'Brief summary of the article...'
            }),
            'status': forms.Select(attrs={
                'class': 'input'
            }),
            'categories': forms.CheckboxSelectMultiple()
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['title'].required = True
        self.fields['content'].required = True
        self.fields['summary'].required = False
        self.fields['categories'].required = False
        self.fields['is_featured'].required = False
        self.fields['is_featured'].widget.attrs.update({'class': 'rounded border-gray-300 text-primary'})


class ProfileForm(forms.ModelForm):
    """Form for updating admin profile"""
    
    current_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Current password'}),
        required=False,
        help_text='Required only if changing password'
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'New password'}),
        required=False
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirm new password'}),
        required=False
    )
    
    class Meta:
        model = Admin
        fields = ['name', 'email']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Email address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get('new_password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if new_password and new_password != confirm_password:
            raise forms.ValidationError('New passwords do not match')
        
        return cleaned_data


class CategoryForm(forms.ModelForm):
    """Form for creating categories"""
    
    class Meta:
        model = Category
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'input',
                'placeholder': 'Category name'
            })
        }


class AdminCreationForm(forms.ModelForm):
    """Form for creating new admin users"""
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Password'}),
        required=True
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'input', 'placeholder': 'Confirm password'}),
        required=True
    )
    
    class Meta:
        model = Admin
        fields = ['name', 'email', 'role']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'input', 'placeholder': 'Full name'}),
            'email': forms.EmailInput(attrs={'class': 'input', 'placeholder': 'Email address'}),
            'role': forms.Select(attrs={'class': 'input'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        confirm_password = cleaned_data.get('confirm_password')
        
        if password and password != confirm_password:
            raise forms.ValidationError('Passwords do not match')
        
        return cleaned_data

    def save(self, commit=True):
        admin = super().save(commit=False)
        admin.set_password(self.cleaned_data['password'])
        if commit:
            admin.save()
        return admin
