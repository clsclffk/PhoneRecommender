from django import forms
from .models import Users

class UserInfoForm(forms.ModelForm):
    class Meta:
        model = Users
        fields = ['nickname', 'gender', 'age_group']
        widgets = {
            'gender': forms.Select(choices=Users.GENDER_CHOICES),
            'age_group': forms.Select(choices=Users.AGE_GROUP_CHOICES),  # 여기서 `10대` → `10s` 값 저장
        }
    
    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        
        # 50자 이내
        if len(nickname) > 50:
            raise forms.ValidationError("닉네임은 최대 50자까지 입력할 수 있습니다.")
        
        # 공백만 입력했을 경우 에러 
        if not nickname.strip():
            raise forms.ValidationError("닉네임에 공백만 입력할 수 없습니다.")
        
        return nickname



