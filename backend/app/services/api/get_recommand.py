from typing import List
from app.models.analyze import Analyze
from supabase import Client
from app.constant import HANGOVER, SOLO, ANNIVERSARY, SIMPLE

def get_category_keywords():
    return {
        "hangover": HANGOVER,
        "solo": SOLO,
        "anniversary": ANNIVERSARY,
        "simple": SIMPLE
    }

def analyze_review_summary(review_summary: str, keywords: List[str]) -> bool:
    # FIXME: 우선 요약문에 키워드가 있는지 확인하는 방식.
    return any(keyword in review_summary for keyword in keywords)

def get_recommendations(supabase: Client, district: str, category: str) -> List[Analyze]:
    try:
        response = supabase.table("analyze")\
            .select(
                "*, restaurants!inner(*)"
            )\
            .eq("analyze.restaurant_id", "restaurants.id")\
            .eq("restaurants.district", district)\
            .execute()
            
        if not response.data:
            return []
            
        category_keywords = get_category_keywords()
        if category not in category_keywords:
            raise ValueError(f"Invalid category: {category}")
            
        recommendations = []
        for item in response.data:
            if analyze_review_summary(item['review_summary'], category_keywords[category]):
                analyze = Analyze(
                    id=item['id'],
                    restaurant_id=item['restaurant_id'],
                    name=item['name'],
                    sentiment_score=item['sentiment_score'],
                    review_summary=item['review_summary'],
                    rating_reliability=item['rating_reliability'],
                    average_rating=item['average_rating'],
                    created_at=item['created_at']
                )
                recommendations.append(analyze)
        
        # 감성 점수 기준으로 정렬
        recommendations.sort(key=lambda x: x.sentiment_score, reverse=True)
        
        return recommendations
        
    except Exception as e:
        print(f"추천 식당 조회 중 오류 발생: {str(e)}")
        return []

def get_category_name(category: str) -> str:
    category_names = {
        "hangover": "해장이 필요해",
        "solo": "빛이나는 Solo",
        "anniversary": "특별한 기념일에 가기 좋은 식당",
        "simple": "한끼는 간단히"
    }
    return category_names.get(category, "")
