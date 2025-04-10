from django.contrib import admin
from .models import Comment, CommentFlag

class CommentFlagInline(admin.TabularInline):
    model = CommentFlag
    extra = 0
    readonly_fields = ['created_at']

class CommentReplyInline(admin.TabularInline):
    model = Comment
    fk_name = 'parent_comment'
    extra = 0
    readonly_fields = ['created_at', 'updated_at']
    fields = ['customer_name', 'content', 'status', 'created_at']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('id', 'entity_type', 'entity_id', 'customer_name', 'short_content', 'rating', 'status', 'created_at')
    list_filter = ('entity_type', 'status', 'created_at', 'is_anonymous')
    search_fields = ('customer_name', 'customer_email', 'content', 'entity_id')
    readonly_fields = ('id', 'created_at', 'updated_at', 'ip_address')
    list_select_related = ('parent_comment',)
    inlines = [CommentReplyInline, CommentFlagInline]
    
    def short_content(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content
    short_content.short_description = 'Content'
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset
    
    def has_replies(self, obj):
        return obj.has_replies
    has_replies.boolean = True
    
    fieldsets = (
        (None, {
            'fields': ('id', 'entity_type', 'entity_id', 'status')
        }),
        ('Customer Information', {
            'fields': ('customer_id', 'customer_name', 'customer_email', 'is_anonymous', 'ip_address')
        }),
        ('Comment Content', {
            'fields': ('content', 'rating', 'parent_comment')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

@admin.register(CommentFlag)
class CommentFlagAdmin(admin.ModelAdmin):
    list_display = ('id', 'comment', 'customer_id', 'reason', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('comment__customer_name', 'comment__content', 'reason')
    readonly_fields = ('id', 'created_at')