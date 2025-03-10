from typing import List
import numpy as np
from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()
client = OpenAI(api_key=os.getenv('AI_KEY'))

def test_analyze_reviews():
    test_reviews = [
        "음식이 정말 맛있었고 서비스도 친절했어요. 다음에 또 방문하고 싶습니다!",
        "위생 상태가 좋지 않았고 음식이 너무 짰어요. 실망했습니다.",
        "가격대비 괜찮은 맛이에요. 보통입니다.",
        "인테리어가 예쁘고 분위기가 좋았어요. 다만 음식이 조금 식어서 나왔네요.",
        "직원분들이 너무 친절하시고 음식도 맛있었어요. 특히 김치찌개가 일품이었습니다!"
    ]
    test_ratings = [4.5, 2.0, 3.0, 3.5, 5.0]

    try:
        print("\n각 리뷰 분석 결과:")
        sentiments = []
        for i, review in enumerate(test_reviews, 1):
            prompt = f"""
다음 식당 리뷰의 감성을 0부터 10까지의 점수로 분석해주세요.
10점이 가장 긍정적이고 0점이 가장 부정적입니다.
숫자만 출력해주세요.

리뷰: {review}

점수:"""
            
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "당신은 식당 리뷰 감성 분석 전문가입니다."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            score = float(response.choices[0].message.content.strip())
            print(f"\n리뷰 {i}: {review}")
            print(f"감성 점수: {score}/10")
            sentiments.append(score)

        avg_sentiment = np.mean(sentiments)
        
        summary_prompt = f"""
다음은 한 식당의 리뷰들입니다. 이 리뷰들을 바탕으로 식당에 대한 한 줄 요약을 작성해주세요.
특히 음식의 맛, 서비스, 분위기 중 자주 언급되는 특징을 중심으로 요약해주세요.

리뷰들:
{' '.join(test_reviews)}

한 줄 요약:"""

        summary_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "당신은 식당 리뷰 분석 전문가입니다."},
                {"role": "user", "content": summary_prompt}
            ],
            temperature=0.7
        )
        
        summary = summary_response.choices[0].message.content.strip()
        
        rating_reliability = 1 - abs(avg_sentiment/10 - np.mean(test_ratings)/5)
        
        return {
            'sentiment_score': avg_sentiment,
            'review_summary': summary,
            'rating_reliability': rating_reliability,
            'average_rating': np.mean(test_ratings),
            'review_count': len(test_reviews)
        }

    except Exception as e:
        print(f"분석 중 오류 발생: {str(e)}")
        return None

if __name__ == "__main__":
    result = test_analyze_reviews()
    if result:
        print("\n최종 분석 결과:", result)
