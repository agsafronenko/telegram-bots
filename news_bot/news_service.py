import requests
from config import Config

class NewsService:
    BASE_URL = 'https://newsapi.org/v2/top-headlines'
    
    @classmethod
    def get_top_headlines(cls, country=None, category=None):
        """
        Fetch top headlines from NewsAPI
        
        :param country: Country code (default from config)
        :param category: News category (default from config)
        :return: List of news articles
        """
        params = {
            'apiKey': Config.NEWS_API_TOKEN,
            'pageSize': Config.MAX_ARTICLES
        }
        
        # Add country if specified, otherwise use default
        if country:
            params['country'] = country
        else:
            params['country'] = Config.DEFAULT_COUNTRY
        
        
        # Add category if specified
        if category:
            params['category'] = category

        print(f"Request parameters: {params}")
        
        try:
            response = requests.get(cls.BASE_URL, params=params)

            response.raise_for_status()
            return response.json().get('articles', [])
        except requests.RequestException as e:
            print(f"Error fetching news: {e}")
            return []