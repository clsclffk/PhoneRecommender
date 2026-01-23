from django.shortcuts import render, redirect
from django.views import View
from django.db import models
import pandas as pd
import json
from hobbies.models import HobbyKeywords 
from analysis.models import AnalysisResults
from users.models import Users
from hobbies.models import HobbyKeywords 
from phone_recommendations.models import PhoneRecommendations
from utils.rag_phone_recommend.pipeline import (
    search_phone_recommendations,
    generate_recommendation_text,
    save_recommendations_to_db
)
from utils.full_analysis_function import get_danawa_avg_scores
from django.utils.safestring import mark_safe
from analysis.tasks import (
    generate_summary_page_1_1,
    generate_summary_page_1_2,
    generate_summary_page_2_1,
    generate_summary_page_2_2,
    generate_summary_page_3,
    run_analysis_step1_task,
    run_analysis_step2_task,
    run_analysis_step3_task, 
    run_analysis_step4_task, 
)

from django.http import JsonResponse
from celery import chain, group
from django.views import View
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.utils.timezone import now
from django.urls import reverse

# 사용자 입력 완료 -> 비동기 작업 시작
class StartAnalysisView(View):
    def get(self, request):
        # GET 요청 들어오면 post 함수로 돌려보내기
        return self.post(request)
    
    def post(self, request):
        print("[DEBUG] POST 데이터:", request.POST)
        # 세션에서 사용자 입력값 가져오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        selected_keywords_str = request.POST.get('selected_keywords')  # 문자열
        selected_keywords = [kw.strip() for kw in selected_keywords_str.split(',') if kw.strip()]  # 리스트로 변환!

        request.session['selected_keywords'] = selected_keywords  # 리스트 형태로 세션에 저장!

        print("hobby_id:", hobby_id)
        print("gender:", gender)
        print("age_group:", age_group)
        print("nickname:", nickname)
        print("selected_keywords:", selected_keywords)

        # 필수값 검증
        if not hobby_id or not gender or not age_group or not nickname or not selected_keywords:
            print("[ERROR] 필수 입력값 누락")
            return redirect('user-info')

        # HobbyKeywords 가져오기
        try:
            hobby_entry = HobbyKeywords.objects.get(hobby_id=hobby_id)
        except HobbyKeywords.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        # 사용자 정보 저장
        user_entry = Users.objects.create(
            nickname=nickname,
            gender=gender,
            age_group=age_group,
            hobby_id=hobby_entry,
            selected_keywords=selected_keywords,
            created_at=now()
        )
        print(f"[INFO] Users 저장 완료: user_id={user_entry.user_id}")

        # 분석 결과 레코드 생성
        analysis_result = AnalysisResults.objects.create(
            hobby_id=hobby_entry,
            selected_keywords=sorted(selected_keywords),
            created_at=now()
        )

        analysis_id = analysis_result.analysis_id
        print(f"[INFO] AnalysisResults 생성 완료: analysis_id={analysis_id}")

        # 세션 저장
        request.session['analysis_id'] = analysis_id
        request.session['selected_keywords'] = selected_keywords
        request.session.modified = True
        request.session.save()

        print("[DEBUG] 세션 저장 완료:", dict(request.session))

        # Celery 비동기 분석 + 추천 실행
        task_args = (analysis_id,)
        analysis_workflow = chain(
            run_analysis_step1_task.si(*task_args),
            group(
                generate_summary_page_1_1.si(*task_args),
                generate_summary_page_1_2.si(*task_args)
            ),
            run_analysis_step2_task.si(*task_args),
            group(
                generate_summary_page_2_1.si(*task_args),
                generate_summary_page_2_2.si(*task_args)
            ),
            run_analysis_step3_task.si(*task_args),
            generate_summary_page_3.si(*task_args),
            run_analysis_step4_task.si(*task_args)
        )
        analysis_workflow.apply_async()

        print(f"[INFO] Celery 비동기 작업 실행 완료: analysis_id={analysis_id}")

        # 분석 결과 1단계 화면으로 이동
        return redirect('analysis-step1')

# 분석 1단계: 키워드 분석 결과 화면
class AnalysisReportStep1View(View):
    def get(self, request):
        # 세션에서 사용자 정보 꺼내오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        selected_keywords = request.session.get('selected_keywords')
        analysis_id = request.session.get('analysis_id')

        # 필수값 검증
        if not hobby_id or not gender or not age_group or not nickname or not selected_keywords:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')
        
        # HobbyKeywords 가져오기 (hobby_id 기준)
        try:
            hobby_entry = HobbyKeywords.objects.get(hobby_id=hobby_id)
        except HobbyKeywords.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        print("[DEBUG] 전체 세션 값:", dict(request.session))
        print(f"[DEBUG] analysis_id from session: {analysis_id}")

        if not analysis_id:
            print("[ERROR] 세션에 analysis_id가 없음!")
            return redirect('hobby-select')

        try:
            analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        except AnalysisResults.DoesNotExist:
            print(f"[ERROR] AnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('hobby-select')

        # 로딩 상태 확인용 처리
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()

            ready = bool(
                analysis_result.summary_page_1_1 and
                analysis_result.summary_page_1_2
            )
            print(f"[DEBUG] status=check 요청 → ready: {ready}")

            return JsonResponse({'ready': ready})
        
        # 분석 결과 준비 여부 체크
        analysis_result.refresh_from_db()

        if not (
            analysis_result.summary_page_1_1 and
            analysis_result.summary_page_1_2
        ):
            print("[INFO] 분석이 아직 완료되지 않음 → 로딩 페이지 렌더링")
            return render(request, 'analysis/loading.html')

        # context는 analysis_result에 있는 데이터 사용
        context = {
            'nickname': nickname,
            'gender': gender,
            'age_group': age_group,
            'gender_kor': {'M': '남성', 'F': '여성'}.get(gender, gender),
            'age_group_kor': {
                '10s': '10대', '20s': '20대', '30s': '30대',
                '40s': '40대', '50s': '50대', '60s': '60대'
            }.get(age_group, age_group),
            'hobby': hobby_entry.hobby_name,
            'selected_keywords': sorted(selected_keywords),
            'samsung_keyword_ratios': analysis_result.freq_ratio_samsung,
            'apple_keyword_ratios': analysis_result.freq_ratio_apple,
            'summary_model1_1': analysis_result.summary_page_1_1,  
            'summary_model1_2': analysis_result.summary_page_1_2,
        }

        return render(request, 'analysis/report_step1.html', context)
        
# 분석 2단계 : 감성 분석
class AnalysisReportStep2View(View):
    def get(self, request):
        # 세션에서 사용자 정보 가져오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        analysis_id = request.session.get('analysis_id')

        # 필수값 검증
        if not hobby_id or not gender or not age_group or not nickname:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')
        
        # HobbyKeywords 가져오기
        try:
            hobby_entry = HobbyKeywords.objects.get(hobby_id=hobby_id)
        except HobbyKeywords.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        hobby_keywords_list = hobby_entry.keyword_list
        hobby_name = hobby_entry.hobby_name

        # AnalysisResults 조회
        try:
            analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        except AnalysisResults.DoesNotExist:
            print(f"[ERROR] AnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        # 폴링 체크 로직
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()
            ready = bool(
                analysis_result.summary_page_2_1 and
                analysis_result.summary_page_2_2
            )
            print(f"[DEBUG] 폴링 체크 - summary_page_2_1: {analysis_result.summary_page_2_1}, summary_page_2_2: {analysis_result.summary_page_2_2}")
            return JsonResponse({'ready': ready})

        analysis_result.refresh_from_db()
        summary_model2_1 = analysis_result.summary_page_2_1
        summary_model2_2 = analysis_result.summary_page_2_2
        print(f"[CHECK] summary_page_2_1: {repr(analysis_result.summary_page_2_1)}")
        print(f"[CHECK] summary_page_2_2: {repr(analysis_result.summary_page_2_2)}")

        if not (analysis_result.summary_page_2_1 and analysis_result.summary_page_2_2):
            print("[DEBUG] 요약 결과 준비되지 않음, 로딩 페이지로 이동")
            return render(request, 'analysis/loading.html')

        # 한글 변환
        age_group_kor = {'10s': '10대', '20s': '20대', '30s': '30대', '40s': '40대', '50s': '50대', '60s': '60대'}.get(age_group, age_group)
        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        selected_keywords = analysis_result.selected_keywords
        sorted_selected_keywords = sorted(selected_keywords)

        # 감성 분석 대표 문장
        sentiment_top_sentences = analysis_result.sentiment_top_sentences or {}

        # 최종 결과 리스트 만들기
        samsung_sentences = []
        apple_sentences = []

        for keyword in sorted_selected_keywords:
            samsung_sentences.append({
                'keyword': keyword,
                'pos': sentiment_top_sentences.get('samsung', {}).get(keyword, {}).get('pos', '데이터 없음'),
                'neg': sentiment_top_sentences.get('samsung', {}).get(keyword, {}).get('neg', '데이터 없음')
            })
            apple_sentences.append({
                'keyword': keyword,
                'pos': sentiment_top_sentences.get('apple', {}).get(keyword, {}).get('pos', '데이터 없음'),
                'neg': sentiment_top_sentences.get('apple', {}).get(keyword, {}).get('neg', '데이터 없음')
            })

        feedback_data = {
            'samsung': {kw: sentiment_top_sentences.get('samsung', {}).get(kw, {'pos': '데이터 없음', 'neg': '데이터 없음'}) for kw in sorted_selected_keywords},
            'apple': {kw: sentiment_top_sentences.get('apple', {}).get(kw, {'pos': '데이터 없음', 'neg': '데이터 없음'}) for kw in sorted_selected_keywords}
        }

        context = {
            'nickname': nickname,
            'gender': gender,
            'age_group': age_group,
            'gender_kor': gender_kor,
            'age_group_kor': age_group_kor,
            'hobby': hobby_name,
            'keyword_list': hobby_keywords_list,
            'selected_keywords': selected_keywords,
            'summary_model2_1': summary_model2_1,
            'summary_model2_2': summary_model2_2,
            'samsung_sentences': samsung_sentences,
            'apple_sentences': apple_sentences,
            'feedback_data_json': json.dumps(feedback_data, ensure_ascii=False),
        }

        return render(request, 'analysis/report_step2.html', context)

# 분석 3단계: 연관어 분석
class AnalysisReportStep3View(View):
    def get(self, request):
        # 세션에서 사용자 정보 가져오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        analysis_id = request.session.get('analysis_id')

        if not hobby_id or not gender or not age_group or not nickname:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')
        if not analysis_id:
            print("[ERROR] analysis_id가 세션에 없음!")
            return redirect('user-info')
        
        # AnalysisResults 가져오기 (analysis_id 기준)
        try:
            analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        except AnalysisResults.DoesNotExist:
            print(f"[ERROR] AnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        # 폴링 체크 로직 추가
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()
            ready = bool(analysis_result.summary_page_3)
            return JsonResponse({'ready': ready})

        analysis_result.refresh_from_db()

        # 요약/연관어 데이터 준비됐는지 확인 → 안됐으면 로딩 페이지
        if not analysis_result.summary_page_3:
            print("[INFO] 분석이 아직 완료되지 않음 → 로딩 페이지 렌더링")
            return render(request, 'analysis/loading.html')

        # 사용자 선택 키워드/취미 정보
        selected_keywords = analysis_result.selected_keywords
        hobby_entry = analysis_result.hobby_id  # FK니까 객체
        hobby_keywords_list = hobby_entry.keyword_list

        # 연령/성별 한글 변환
        age_group_kor = {'10s': '10대', '20s': '20대', '30s': '30대', '40s': '40대', '50s': '50대', '60s': '60대'}.get(age_group, age_group)
        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        # 연관어 데이터 가져오기
        related_words_samsung = analysis_result.related_words_samsung or {}
        related_words_apple = analysis_result.related_words_apple or {}

        samsung_keywords = related_words_samsung.get('related_words', [])
        apple_keywords = related_words_apple.get('related_words', [])

        # 최종 context
        context = {
            # 사용자 정보
            'nickname': nickname,
            'gender_kor': gender_kor,
            'age_group_kor': age_group_kor,
            'hobby': hobby_entry.hobby_name,  # hobby_id 기준
            'keyword_list': hobby_keywords_list,
            'selected_keywords': selected_keywords,

            # 분석 결과
            'samsung_keywords': samsung_keywords,
            'apple_keywords': apple_keywords,
            'summary_model3': analysis_result.summary_page_3,
        }

        return render(request, 'analysis/report_step3.html', context)
    
# 분석 4단계: 실 구매평 + 폰 추천
class AnalysisReportStep4View(View):
    def get(self, request):
        # 세션에서 값 가져오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        analysis_id = request.session.get('analysis_id')

        # 필수값 검증
        if not hobby_id or not gender or not age_group or not nickname or not analysis_id:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')

        # HobbyKeywords 가져오기
        try:
            hobby_entry = HobbyKeywords.objects.get(hobby_id=hobby_id)
        except HobbyKeywords.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        hobby_keywords_list = hobby_entry.keyword_list
        hobby_name = hobby_entry.hobby_name

        # AnalysisResults 가져오기
        try:
            analysis_result = AnalysisResults.objects.get(analysis_id=analysis_id)
        except AnalysisResults.DoesNotExist:
            print(f"[ERROR] AnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        # 선택 키워드 정렬
        selected_keywords = sorted(analysis_result.selected_keywords)

        print(f"[DEBUG] 조회 전: hobby_id={hobby_id}, selected_keywords={selected_keywords}")

        # 추천 결과 조회 (필요 시 gender/age_group도 추가 필터 가능)
        phone_recommendation = PhoneRecommendations.objects.filter(
            hobby_id=hobby_id,
            selected_keywords=selected_keywords
        ).first()

        print(f"[DEBUG] 추천 검색! hobby_id: {hobby_id}, keywords: {selected_keywords}")
        print(f"[DEBUG] 추천 결과: {phone_recommendation}")

        # 폴링 체크
        if request.GET.get('status') == 'check':
            ready = bool(phone_recommendation)
            return JsonResponse({'ready': ready})

        if not phone_recommendation:
            print("[INFO] 추천 결과가 아직 없음 → 로딩 화면 이동")
            return render(request, 'analysis/loading.html')

        # 추천 결과 처리
        recommendation_text_raw = phone_recommendation.recommendations.get(
            'recommendations', "추천 결과가 없습니다."
        )

        recommendation_lines = [
            line.strip() for line in recommendation_text_raw.strip().split('\n')
            if line.strip()
        ]

        recommendation_list = []
        for line in recommendation_lines:
            line_no_prefix = line.split(". ", 1)[-1]
            phone_info = line_no_prefix.split(" - ")

            if len(phone_info) == 2:
                phone_name, reason = phone_info
                recommendation_list.append({
                    "phone_name": phone_name.strip(),
                    "reason": reason.strip()
                })
            else:
                recommendation_list.append({
                    "phone_name": line_no_prefix.strip(),
                    "reason": ""
                })

        # 다나와 점수 가져오기
        avg_scores = get_danawa_avg_scores()
        samsung_score = avg_scores.get('samsung', 0)
        apple_score = avg_scores.get('apple', 0)

        # 한글 변환
        age_group_kor = {
            '10s': '10대', '20s': '20대', '30s': '30대',
            '40s': '40대', '50s': '50대', '60s': '60대'
        }.get(age_group, age_group)

        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        context = {
            'nickname': nickname,
            'gender_kor': gender_kor,
            'age_group_kor': age_group_kor,
            'hobby': hobby_name,  # hobby_id 기준에서 가져온 name
            'keyword_list': hobby_keywords_list,
            'selected_keywords': selected_keywords,
            'recommendation_list': recommendation_list,
            'samsung_score': int(samsung_score),
            'apple_score': int(apple_score),
        }

        return render(request, 'analysis/report_step4.html', context)