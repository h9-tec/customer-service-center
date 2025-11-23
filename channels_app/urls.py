from django.urls import path

from channels_app import views

urlpatterns = [
    path('whatsapp/', views.WhatsAppWebhookView.as_view(), name='whatsapp-webhook'),
    path('whatsapp/send/', views.OutboundWhatsAppMessageView.as_view(), name='whatsapp-send'),
    path('whatsapp/messages/html/', views.whatsapp_messages_html, name='whatsapp-messages-html'),
    path('shopify/', views.ShopifyWebhookView.as_view(), name='shopify-webhook'),
    path('magento/', views.MagentoWebhookView.as_view(), name='magento-webhook'),
]
