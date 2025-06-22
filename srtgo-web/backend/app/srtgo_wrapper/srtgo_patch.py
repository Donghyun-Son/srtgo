"""
SRTgo 모듈의 호환성 문제를 해결하기 위한 패치
"""
import sys

def patch_srtgo_modules():
    """SRTgo 모듈의 impersonate 버전을 패치"""
    # srt.py의 Session 생성 부분을 monkey patch
    try:
        import curl_cffi
        from curl_cffi.requests import Session
        
        # 원본 Session 클래스 저장
        _original_session_init = Session.__init__
        
        def patched_session_init(self, *args, **kwargs):
            # chrome131_android를 chrome110으로 변경
            if 'impersonate' in kwargs:
                if kwargs['impersonate'] == 'chrome131_android':
                    kwargs['impersonate'] = 'chrome110'
            _original_session_init(self, *args, **kwargs)
        
        # Monkey patch 적용
        Session.__init__ = patched_session_init
        curl_cffi.Session = Session
        
        print("curl_cffi Session patched successfully")
        
    except Exception as e:
        print(f"Failed to patch curl_cffi Session: {e}")
    
