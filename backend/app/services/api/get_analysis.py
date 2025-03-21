from typing import Optional, List
from app.models.analyze import Analyze
from supabase import Client

def get_analysis_with_district(supabase: Client, district: str) -> List[Analyze]:
    try:
        response = supabase.table("analyze")\
            .select(
                "*, restaurants(*)"
            )\
            .eq("restaurants.district", district)\
            .execute()
            
        if not response.data:
            return []
            
        analysis = []
        for item in response.data:
            analyze_data = {
                'id': item['id'],
                'restaurant_id': item['restaurant_id'],
                'name': item['name'],
                'sentiment_score': item['sentiment_score'],
                'review_summary': item['review_summary'],
                'rating_reliability': item['rating_reliability'],
                'average_rating': item['average_rating'],
                'created_at': item['created_at']
            }
            analysis.append(Analyze(**analyze_data))
            
        return analysis
        
    except Exception as e:
        print(f"분석 결과 조회 중 오류 발생: {str(e)}")
        return []
