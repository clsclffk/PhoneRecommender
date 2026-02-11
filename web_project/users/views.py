from django.shortcuts import render, redirect
from django.views import View
from .models import TbUsers
from hobbies.models import TbHobbies
from utils.db_connection import check_hobby
from utils.llm_api import get_keyword
from django.utils.timezone import now
from django.contrib import messages
from django.http import HttpResponse

# 사용자 기본 정보 입력 (닉네임, 성별, 나이)
# 세션 저장
# 취미 선택 페이지로 이동
class UserInfoView(View):
    def get(self, request):
        return render(request, 'users/user_info.html')

    def post(self, request):
        nickname = request.POST.get("nickname")
        age_group = request.POST.get("age_group")
        gender = request.POST.get("gender")

        if not nickname or not age_group or not gender:
            return render(request, 'users/user_info.html', {"error": "모든 정보를 입력하세요!"})

        # 세션 저장
        request.session['user_nickname'] = nickname
        request.session['age_group'] = age_group
        request.session['gender'] = gender

        return redirect('hobby-select')
    
# 사용자가 고정된 9개 취미 중 선택하거나 추천으로 넘어가는 페이지
class HobbySelectView(View):
    def get(self, request):
        if not request.session.get('user_nickname'):
            return redirect('user-info')
        
        # 세션에서 사용자 정보 가져오기
        age_group = request.session.get('age_group')
        gender = request.session.get('gender')

        # TbHobbies에서 취미 목록 조회 (최대 9개)
        recommended_hobbies = list(TbHobbies.objects.values_list('hobby_name', flat=True)[:9])
        if len(recommended_hobbies) < 9:
            # 기본 취미로 채우기
            default_hobbies = ['음악 감상', '여행', '운동', '게임', '독서', '사진 촬영', '영상시청', '요리', '등산']
            for h in default_hobbies:
                if h not in recommended_hobbies:
                    recommended_hobbies.append(h)
                if len(recommended_hobbies) >= 9:
                    break
            recommended_hobbies = recommended_hobbies[:9]

        context = {
            "recommended_hobbies": recommended_hobbies,
            "age_group": age_group,
            "gender": gender
        }

        return render(request, 'users/hobby_select.html', context)

    def post(self, request):
        # 버튼에 따라 분기
        action_type = request.POST.get('action_type')

        if action_type == 'next':  # '다음' 버튼 눌렀을 때
            selected_hobby = request.POST.get('selected_hobby', "").strip()

            if not selected_hobby:
                return render(request, 'users/hobby_select.html', {"error": "취미를 선택해주세요."})
 
            # 세션에 저장하고 키워드 선택 페이지로 이동
            request.session['selected_hobby'] = selected_hobby
            return redirect('keyword-select')

        elif action_type == 'recommend':  # '다른 취미 살펴보기' 버튼 눌렀을 때
            return redirect('recommend-hobby')

        # 예외 처리
        return render(request, 'users/hobby_select.html', {"error": "잘못된 접근입니다."})

# 추천 취미 보여주고 선택하게 하거나 사용자 직접 입력
class RecommendHobbyView(View):
    def get(self, request):
        # 세션에서 사용자 기본 정보 확인
        nickname = request.session.get('user_nickname')
        age_group = request.session.get('age_group')
        gender = request.session.get('gender')

        # 필수 정보가 없으면 다시 시작
        if not (nickname and age_group and gender):
            return redirect('user-info')
        
        age_group_display = {
            '10s': '10대',
            '20s': '20대',
            '30s': '30대',
            '40s': '40대',
            '50s': '50대',
            '60s': '60대'
        }

        gender_display = {
            'M': '남성',
            'F': '여성'
        }

        age_group_kor = age_group_display.get(age_group, age_group)
        gender_kor = gender_display.get(gender, gender)

        # TbHobbies에서 취미 목록 조회 (상위 3개) 또는 기본값
        hobby_list = list(TbHobbies.objects.values_list('hobby_name', flat=True)[:3])
        recommended_hobbies = hobby_list if len(hobby_list) >= 3 else ['음악 감상', '여행', '운동']

        # 추천된 취미 리스트 만들기
        print("Recommended Hobbies:", recommended_hobbies)
        context = {
            "nickname": nickname,
            "age_group": age_group,
            "gender": gender,
            "age_group_display": age_group_kor,
            "gender_display": gender_kor,
            "recommended_hobbies": recommended_hobbies,
        }

        return render(request, 'users/recommend_hobby.html', context)

    def post(self, request):
        # 세션에서 사용자 기본 정보 확인
        nickname = request.session.get('user_nickname')
        age_group = request.session.get('age_group')
        gender = request.session.get('gender')
        print("[DEBUG] nickname:", nickname)
        print("[DEBUG] age_group:", age_group)
        print("[DEBUG] gender:", gender)

        if not (nickname and age_group and gender):
            return redirect('user-info')

        # 사용자가 추천에서 선택한 취미
        selected_hobby = request.POST.get('selected_hobby', "").strip()

        # 사용자가 직접 입력한 취미
        custom_hobby = request.POST.get('custom_hobby', "").strip()

        # 사용자가 직접 입력한 값이 우선
        final_hobby = custom_hobby if custom_hobby else selected_hobby

        if not final_hobby:
            # 선택 안 했으면 다시 추천 취미로 돌아감
            return render(request, 'users/recommend_hobby.html', {
                "error": "취미를 선택하거나 입력해주세요."
            })

        # 세션에 최종 선택한 취미 저장
        request.session['selected_hobby'] = final_hobby
        request.session.modified = True

        # 다음 단계로 이동 (키워드 선택 페이지)
        return redirect('keyword-select')


# 기능 키워드 3~5개 선택 & Users, HobbyTrends 저장
class KeywordSelectView(View):
    def get(self, request):
        # 세션에서 기본 정보 꺼내오기
        nickname = request.session.get('user_nickname')
        age_group = request.session.get('age_group')
        gender = request.session.get('gender')
        selected_hobby = request.session.get('selected_hobby')

        # 필수 정보가 없으면 처음으로 리디렉션
        if not (nickname and age_group and gender and selected_hobby):
            return redirect('user-info')

        # 해당 취미가 tb_hobbies에 존재하는지 확인 (없으면 LLM 호출 포함된 check_hobby 함수)
        hobby_id = check_hobby(selected_hobby)
        if hobby_id is None:
            print("[ERROR] hobby_id 못 찾음 → hobby-select로 이동")
            return redirect('hobby-select')
        # 세션 저장 추가!
        request.session['hobby_id'] = hobby_id
        request.session.modified = True
        request.session.save()

        # 추천 키워드는 LLM으로 생성 (TbHobbies에는 keyword_list 없음)
        recommended_keywords = get_keyword(selected_hobby) or []

        context = {
            "selected_hobby": selected_hobby,
            "recommended_keywords": recommended_keywords
        }

        return render(request, 'users/keyword_select.html', context)

    def post(self, request):
        # 세션에서 기본 정보 꺼내오기
        nickname = request.session.get('user_nickname')
        age_group = request.session.get('age_group')
        gender = request.session.get('gender')
        selected_hobby = request.session.get('selected_hobby')
        hobby_id = request.session.get('hobby_id')

        if not (nickname and age_group and gender and selected_hobby):
            return redirect('user-info')

        if not hobby_id:
            hobby_id = check_hobby(selected_hobby)
            if hobby_id is None:
                print("[ERROR] POST → hobby_id 못 찾음")
                return redirect('hobby-select')

        request.session['hobby_id'] = hobby_id
        request.session.modified = True
        request.session.save()

        recommended_keywords = get_keyword(selected_hobby) or []

        # 선택한 키워드 리스트 받아오기
        selected_keywords_str = request.POST.get('selected_keywords', '')
        selected_keywords = [kw.strip() for kw in selected_keywords_str.split(',') if kw.strip()]

        if not (3 <= len(selected_keywords) <= 5):
            return render(request, 'users/keyword_select.html', {
                "selected_hobby": selected_hobby,
                "recommended_keywords": recommended_keywords,
                "error": "키워드는 최소 3개에서 최대 5개까지 선택해야 합니다."
            })

        # TbUsers 테이블에 저장 (닉네임, 연령대, 성별만 저장)
        user = TbUsers.objects.create(
            nickname=nickname,
            age_group=age_group,
            gender=gender
        )
        print(f"[DEBUG] 사용자 저장 완료! user_id={user.user_id}")

        # 세션에 정보 저장 (추후 분석에서 활용)
        request.session['hobby_id'] = hobby_id
        request.session['selected_keywords'] = selected_keywords
        request.session.modified = True
        request.session.save()

        # 분석 리포트 페이지로 리디렉션
        return redirect('start-analysis')


