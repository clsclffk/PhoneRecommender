from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": AuthMiddlewareStack(
        URLRouter([
            # 여기에 웹소켓 경로가 추가될 수 있음 (지금은 기본만)
        ])
    ),
})
