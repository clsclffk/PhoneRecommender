from django.shortcuts import render

def main_page(request):
    request.session.flush()  # 세션 초기화
    return render(request, 'main.html')

def guide_page(request):
    request.session.flush()  # 세션 초기화
    return render(request, 'guide.html')