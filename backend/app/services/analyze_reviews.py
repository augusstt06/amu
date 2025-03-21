# FIXME: 프롬포트 수정하기.
from typing import List
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv
import time
from tenacity import retry, stop_after_attempt, wait_exponential

load_dotenv()
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def analyze_single_review(review: str) -> float:
    prompt = f"""
다음 식당 리뷰의 감성을 0부터 10까지의 점수로 분석해주세요.
10점이 가장 긍정적이고 0점이 가장 부정적입니다.
숫자만 출력해주세요.

리뷰: {review}

점수:"""
    
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "당신은 식당 리뷰 감성 분석 전문가입니다. 반드시 0부터 10 사이의 숫자만 출력해주세요."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        timeout=30  
    )
    
    score_text = response.choices[0].message.content.strip()
    score_text = ''.join(filter(lambda x: x.isdigit() or x == '.', score_text))
    
    try:
        score = float(score_text)
        return max(0, min(10, score)) 
    except ValueError:
        return 5.0 

def analyze_reviews(review_texts: List[str], ratings: List[float]) -> dict:
    try:
        print("\n각 리뷰 분석 결과:")
        sentiments = []
        total_reviews = len(review_texts)
        
        for i, review in enumerate(review_texts, 1):
            print(f"\r리뷰 분석 중... {i}/{total_reviews}", end="")
            try:
                score = analyze_single_review(review)
                sentiments.append(score)
                time.sleep(1)  
            except Exception as e:
                print(f"\n⚠️ 리뷰 분석 실패: {str(e)}, 기본값 5.0 사용")
                sentiments.append(5.0)

        print()  # 줄바꿈

        avg_sentiment = np.mean(sentiments)
        avg_rating = np.mean(ratings) if ratings else 0.0
        
        summary_prompt = f"""
다음은 한 식당의 여러 리뷰들입니다. 이 리뷰들을 바탕으로 식당을 한 문장(공백을 포함한 80자 이내)으로 요약해주세요.
다음 형식으로 작성해주세요: "[대표 특징]이 돋보이는 [음식 종류]. [대표 메뉴나 장점] 추천" 형식으로 작성하고, 주요 단점이 있다면 마지막에 ". 다만, [단점]" 형식으로 추가해주세요.

예시:
- 분위기가 좋은 족발 맛집. 매콤한 양념족발이 일품. 다만, 가격대가 높은 편
- 가성비 좋은 일식당. 신선한 회와 사케동 추천. 다만, 웨이팅이 긴 편
- 정갈한 한정식 맛집. 계절 반찬이 특히 훌륭하지만, 주차가 불편
- 전통적인 중식당. 짜장면과 탕수육 맛이 일품 (단점 없는 경우 생략)

리뷰들:
{' '.join(review_texts)}

한 문장 요약:"""

        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 식당 리뷰 요약 전문가입니다. 장점 위주로 요약하되, 주요 단점이 있다면 마지막에 추가해주세요."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7
        )
        
        summary = summary_response.choices[0].message.content.strip()
        
        return {
            'sentiment_score': avg_sentiment,
            'review_summary': summary,
            'review_count': len(review_texts),
            'average_rating': avg_rating
        }

    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    result = analyze_reviews()
    # if result:
    #     print("\n최종 분석 결과:", result)
