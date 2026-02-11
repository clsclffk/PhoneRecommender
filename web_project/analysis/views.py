from django.shortcuts import render, redirect
from django.views import View
from django.db import models
import pandas as pd
import json
import hashlib
from hobbies.models import TbHobbies
from analysis.models import TbAnalysisResults
from users.models import TbUsers
from phone_recommendations.models import PhoneRecommendations
from utils.rag_phone_recommend.pipeline import (
    search_phone_recommendations,
    generate_recommendation_text,
    save_recommendations_to_db
)
from utils.full_analysis_function import get_danawa_avg_scores, generate_keywords_hash
from django.utils.safestring import mark_safe


def _summaries_dict(obj):
    """TbAnalysisResults.summaries JSON 파싱"""
    if not obj or not getattr(obj, 'summaries', None):
        return {}
    try:
        return json.loads(obj.summaries) if isinstance(obj.summaries, str) else (obj.summaries or {})
    except (json.JSONDecodeError, TypeError):
        return {}
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
from utils.timer_decorator import timer


# 사용자 입력 완료 -> 비동기 작업 시작
class StartAnalysisView(View):
    def get(self, request):
        return self.post(request)
        
    @timer
    def post(self, request):
        print("[DEBUG] POST 데이터:", request.POST)
        
        # 세션에서 사용자 입력값 가져오기
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        selected_keywords_str = request.POST.get('selected_keywords')
        selected_keywords = [kw.strip() for kw in selected_keywords_str.split(',') if kw.strip()]

        request.session['selected_keywords'] = selected_keywords
        
        print("hobby_id:", hobby_id)
        print("selected_keywords:", selected_keywords)

        # 필수값 검증
        if not hobby_id or not gender or not age_group or not nickname or not selected_keywords:
            print("[ERROR] 필수 입력값 누락")
            return redirect('user-info')

        # TbHobbies 가져오기
        try:
            hobby_entry = TbHobbies.objects.get(hobby_id=hobby_id)
        except TbHobbies.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        # 키워드 해시 생성 (정렬 후)
        sorted_keywords = sorted(selected_keywords)
        keywords_hash = generate_keywords_hash(sorted_keywords)
        
        # 기존 분석 결과 조회 (해시 기반)
        existing_result = TbAnalysisResults.objects.filter(
            hobby=hobby_entry,
            keywords_hash=keywords_hash,
            age_group=age_group,
            gender=gender
        ).first()
        
        if existing_result:
            print(f"[INFO] 기존 분석 결과 발견: analysis_id={existing_result.analysis_id}")
            request.session['analysis_id'] = existing_result.analysis_id
            return redirect('analysis-step1')

        # 사용자 정보 저장 (TbUsers: 닉네임, 성별, 연령대만)
        user_entry = TbUsers.objects.create(
            nickname=nickname,
            gender=gender,
            age_group=age_group
        )
        print(f"[INFO] TbUsers 저장 완료: user_id={user_entry.user_id}")

        # 분석 결과 레코드 생성 (해시는 save()에서 자동 생성)
        analysis_result = TbAnalysisResults.objects.create(
            hobby=hobby_entry,
            keywords=sorted_keywords,
            age_group=age_group,
            gender=gender
        )

        analysis_id = analysis_result.analysis_id
        print(f"[INFO] AnalysisResults 생성 완료: analysis_id={analysis_id}")

        # 세션 저장
        request.session['analysis_id'] = analysis_id
        request.session['selected_keywords'] = sorted_keywords
        request.session.modified = True
        request.session.save()

        # Celery 비동기 작업
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

        return redirect('analysis-step1')


# 분석 1단계: 키워드 분석 결과 화면
class AnalysisReportStep1View(View):
    @timer
    def get(self, request):
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        selected_keywords = request.session.get('selected_keywords')
        analysis_id = request.session.get('analysis_id')

        if not hobby_id or not gender or not age_group or not nickname or not selected_keywords:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')
        
        try:
            hobby_entry = TbHobbies.objects.get(hobby_id=hobby_id)
        except TbHobbies.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        if not analysis_id:
            print("[ERROR] 세션에 analysis_id가 없음!")
            return redirect('hobby-select')

        try:
            analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        except TbAnalysisResults.DoesNotExist:
            print(f"[ERROR] TbAnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('hobby-select')

        summaries = _summaries_dict(analysis_result)
        freq_ratios = analysis_result.freq_ratios or {}
        samsung_ratios = freq_ratios.get('samsung', {})
        apple_ratios = freq_ratios.get('apple', {})

        # 폴링 체크
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()
            summaries = _summaries_dict(analysis_result)
            ready = bool(
                summaries.get('summary_page_1_1') and
                summaries.get('summary_page_1_2')
            )
            return JsonResponse({'ready': ready})
        
        analysis_result.refresh_from_db()
        summaries = _summaries_dict(analysis_result)
        freq_ratios = analysis_result.freq_ratios or {}
        samsung_ratios = freq_ratios.get('samsung', {})
        apple_ratios = freq_ratios.get('apple', {})

        if not (summaries.get('summary_page_1_1') and summaries.get('summary_page_1_2')):
            print("[INFO] 분석이 아직 완료되지 않음 → 로딩 페이지")
            return render(request, 'analysis/loading.html')

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
            'samsung_keyword_ratios': samsung_ratios,
            'apple_keyword_ratios': apple_ratios,
            'summary_model1_1': summaries.get('summary_page_1_1', ''),
            'summary_model1_2': summaries.get('summary_page_1_2', ''),
        }

        return render(request, 'analysis/report_step1.html', context)


# 분석 2단계 : 감성 분석
class AnalysisReportStep2View(View):
    @timer
    def get(self, request):
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        analysis_id = request.session.get('analysis_id')

        if not hobby_id or not gender or not age_group or not nickname:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')
        
        try:
            hobby_entry = TbHobbies.objects.get(hobby_id=hobby_id)
        except TbHobbies.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        try:
            analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        except TbAnalysisResults.DoesNotExist:
            print(f"[ERROR] TbAnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        summaries = _summaries_dict(analysis_result)
        sentiment_top_sentences = summaries.get('sentiment_top_sentences') or {}

        # 폴링 체크
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()
            summaries = _summaries_dict(analysis_result)
            ready = bool(summaries.get('summary_page_2_1') and summaries.get('summary_page_2_2'))
            return JsonResponse({'ready': ready})

        analysis_result.refresh_from_db()
        summaries = _summaries_dict(analysis_result)
        sentiment_top_sentences = summaries.get('sentiment_top_sentences') or {}

        if not (summaries.get('summary_page_2_1') and summaries.get('summary_page_2_2')):
            return render(request, 'analysis/loading.html')

        age_group_kor = {'10s': '10대', '20s': '20대', '30s': '30대', '40s': '40대', '50s': '50대', '60s': '60대'}.get(age_group, age_group)
        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        selected_keywords = analysis_result.keywords or []
        sorted_selected_keywords = sorted(selected_keywords)

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
            'hobby': hobby_entry.hobby_name,
            'keyword_list': [],  # TbHobbies에는 keyword_list 없음
            'selected_keywords': selected_keywords,
            'summary_model2_1': summaries.get('summary_page_2_1', ''),
            'summary_model2_2': summaries.get('summary_page_2_2', ''),
            'samsung_sentences': samsung_sentences,
            'apple_sentences': apple_sentences,
            'feedback_data_json': json.dumps(feedback_data, ensure_ascii=False),
        }

        return render(request, 'analysis/report_step2.html', context)


# 분석 3단계: 연관어 분석
class AnalysisReportStep3View(View):
    @timer
    def get(self, request):
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
        
        try:
            analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        except TbAnalysisResults.DoesNotExist:
            print(f"[ERROR] TbAnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        summaries = _summaries_dict(analysis_result)
        related_words_samsung = summaries.get('related_words_samsung') or {}
        related_words_apple = summaries.get('related_words_apple') or {}

        # 폴링 체크
        if request.GET.get('status') == 'check':
            analysis_result.refresh_from_db()
            summaries = _summaries_dict(analysis_result)
            return JsonResponse({'ready': bool(summaries.get('summary_page_3'))})

        analysis_result.refresh_from_db()
        summaries = _summaries_dict(analysis_result)
        related_words_samsung = summaries.get('related_words_samsung') or {}
        related_words_apple = summaries.get('related_words_apple') or {}

        if not summaries.get('summary_page_3'):
            return render(request, 'analysis/loading.html')

        selected_keywords = analysis_result.keywords or []
        hobby_entry = analysis_result.hobby

        age_group_kor = {'10s': '10대', '20s': '20대', '30s': '30대', '40s': '40대', '50s': '50대', '60s': '60대'}.get(age_group, age_group)
        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        samsung_keywords = related_words_samsung.get('related_words', [])
        apple_keywords = related_words_apple.get('related_words', [])

        context = {
            'nickname': nickname,
            'gender_kor': gender_kor,
            'age_group_kor': age_group_kor,
            'hobby': hobby_entry.hobby_name,
            'keyword_list': [],
            'selected_keywords': selected_keywords,
            'samsung_keywords': samsung_keywords,
            'apple_keywords': apple_keywords,
            'summary_model3': summaries.get('summary_page_3', ''),
        }

        return render(request, 'analysis/report_step3.html', context)


# 분석 4단계: 실 구매평 + 폰 추천
class AnalysisReportStep4View(View):
    @timer
    def get(self, request):
        hobby_id = request.session.get('hobby_id')
        gender = request.session.get('gender')
        age_group = request.session.get('age_group')
        nickname = request.session.get('user_nickname')
        analysis_id = request.session.get('analysis_id')

        if not hobby_id or not gender or not age_group or not nickname or not analysis_id:
            print("[ERROR] 필수 세션 값 누락")
            return redirect('user-info')

        try:
            hobby_entry = TbHobbies.objects.get(hobby_id=hobby_id)
        except TbHobbies.DoesNotExist:
            print(f"[ERROR] 존재하지 않는 hobby_id: {hobby_id}")
            return redirect('hobby-select')

        try:
            analysis_result = TbAnalysisResults.objects.get(analysis_id=analysis_id)
        except TbAnalysisResults.DoesNotExist:
            print(f"[ERROR] TbAnalysisResults 없음! analysis_id={analysis_id}")
            return redirect('user-info')

        selected_keywords = sorted(analysis_result.keywords or [])

        phone_recommendation = PhoneRecommendations.objects.filter(
            hobby_id=hobby_entry,
            selected_keywords=selected_keywords
        ).first()

        # 폴링 체크
        if request.GET.get('status') == 'check':
            ready = bool(phone_recommendation)
            return JsonResponse({'ready': ready})

        if not phone_recommendation:
            return render(request, 'analysis/loading.html')

        rec = phone_recommendation.recommendations
        if isinstance(rec, dict):
            recommendation_text_raw = rec.get('recommendations', "추천 결과가 없습니다.")
        else:
            recommendation_text_raw = rec or "추천 결과가 없습니다."

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

        avg_scores = get_danawa_avg_scores()
        samsung_score = avg_scores.get('samsung', 0)
        apple_score = avg_scores.get('apple', 0)

        age_group_kor = {
            '10s': '10대', '20s': '20대', '30s': '30대',
            '40s': '40대', '50s': '50대', '60s': '60대'
        }.get(age_group, age_group)

        gender_kor = {'M': '남성', 'F': '여성'}.get(gender, gender)

        context = {
            'nickname': nickname,
            'gender_kor': gender_kor,
            'age_group_kor': age_group_kor,
            'hobby': hobby_entry.hobby_name,
            'keyword_list': [],
            'selected_keywords': selected_keywords,
            'recommendation_list': recommendation_list,
            'samsung_score': int(samsung_score),
            'apple_score': int(apple_score),
        }

        return render(request, 'analysis/report_step4.html', context)