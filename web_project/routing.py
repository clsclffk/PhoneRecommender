from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    "websocket": AuthMiddlewareStack(
        URLRouter([
            
        ])
    ),
})
