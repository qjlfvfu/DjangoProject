from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse_lazy
from blog.models import Blog
from django.views.generic import ListView, DetailView, UpdateView, DeleteView,CreateView


class BlogListView(ListView):
    model = Blog
    template_name = 'blog/blog_list.html'
    context_object_name = 'blogs'
    paginate_by = 10

    def get_queryset(self):
        # ✅ Только опубликованные статьи
        return Blog.objects.filter(is_published=True).order_by('-created_at')


class BlogDetailView(DetailView):
    model = Blog
    template_name = 'blog/blog_detail.html'
    context_object_name = 'blog'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # ✅ Увеличение счетчика просмотров
        self.object.views_count += 1
        self.object.save(update_fields=['views_count'])
        return context

    def get_object(self, queryset=None):
        """Получаем объект и увеличиваем счетчик просмотров АТОМАРНО"""
        # Получаем объект стандартным способом
        obj = super().get_object(queryset)
        Blog.objects.filter(pk=obj.pk).update(
            views_count=F('views_count') + 1
        )

        # Обновляем объект из базы данных
        obj.refresh_from_db()

        return obj


class BlogCreateView(CreateView):
    model = Blog
    template_name = 'blog/blog_form.html'
    fields = ['name', 'description', 'preview', 'is_published']
    success_url = reverse_lazy('blog:blog_list')

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)


class BlogUpdateView(UpdateView):
    model = Blog
    template_name = 'blog/blog_form.html'
    fields = ['name', 'description', 'preview', 'is_published']

    def get_success_url(self):
        """Перенаправляем на страницу отредактированной статьи"""
        return reverse_lazy('blog:blog_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        """Действия при успешном обновлении"""
        messages.success(self.request, 'Статья успешно обновлена!')
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        """Добавляем информацию о том, что это редактирование"""
        context = super().get_context_data(**kwargs)
        context['is_update'] = True
        return context


# ✅ Удаление
class BlogDeleteView(DeleteView):
    model = Blog
    template_name = 'blog/blog_confirm_delete.html'
    success_url = reverse_lazy('blog:blog_list')