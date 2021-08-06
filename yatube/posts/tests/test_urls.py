from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls.base import reverse

from ..models import Group, Post

User = get_user_model()


class PostURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leo = User.objects.create(username='leo')
        cls.test_post_one = Post.objects.create(
            text='Тестовый пост',
            author=cls.leo
        )
        cls.test_group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test group for test'
        )

    def setUp(self):
        self.guest_client = Client()
        self.post_author = User.objects.create_user(username='author')
        self.post_not_author = User.objects.create_user(username='not_author')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.post_author)
        self.authorized_non_author_client = Client()
        self.authorized_non_author_client.force_login(self.post_not_author)
        self.test_post = Post.objects.create(
            text='Тестовый пост',
            author=self.post_author
        )
        self.posts_urls = {
            'posts/index.html': '/',
            'posts/group.html': f'/group/{PostURLTests.test_group.slug}/',
            'posts/profile.html': f'/{PostURLTests.leo.username}/',
            'posts/post.html':
            f'/{PostURLTests.leo.username}/{PostURLTests.test_post_one.id}/'

        }

    def test_urls_uses_correct_template(self):
        """Url-адреса используют соответствующий шаблон"""
        for template, adress in self.posts_urls.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(
                    response, template, 'Ошибка с шаблонами')

    def test_new_post_url_uses_correct_template(self):
        """Url-адрес new_post использует соответствующий шаблон"""
        response = self.authorized_client.get('/new/')
        self.assertTemplateUsed(
            response, 'posts/new.html', 'Некорректный шаблон new_post'
        )

    def test_edit_post_uses_correct_template(self):
        """Url-адрес edit_post использует соответствующий шаблон"""
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }),
        )
        self.assertTemplateUsed(
            response, 'posts/new.html', 'Некорректный шаблон new_post'
        )

    def test_urls_exist_at_desired_location(self):
        """Url-адреса существуют по заданному адресу"""
        for template, adress in self.posts_urls.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertEqual(
                    response.status_code, 200, 'Адрес недоступен')

    def test_new_post_url_access(self):
        """Гостевой клиент переадресуется правильно"""
        response = self.guest_client.get('/new/')
        self.assertEqual(
            response.status_code, 302,
            'Ошибка переадресации с гостевого клиента')

    def test_new_post_authorized_access(self):
        """Авторизованный клиент имеет доступ к странице нового поста"""
        response = self.authorized_client.get('/new/')
        self.assertEqual(
            response.status_code, 200, 'Ошибка доступа авторизованого клиента')

    def test_post_author_access(self):
        """Доступ к редактированию поста имеет только автор"""
        response = self.authorized_client.get(
            reverse('post_edit', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }),
        )
        self.assertEqual(
            response.status_code, 200, 'Автор поста не имеет доступа к посту')

    def test_not_post_author_access(self):
        """Не автор не имеет доступа к редактированию поста"""
        response = self.authorized_non_author_client.get(
            reverse('post_edit', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }),
        )
        self.assertEqual(
            response.status_code, 302, 'Не автор поста имеет доступ к посту')

    def test_guest_client_access(self):
        """Гостевой клиент не имеет доступа к редактированию поста"""
        response = self.guest_client.get(
            reverse('post_edit', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }),
        )
        self.assertEqual(
            response.status_code, 302, 'Гостевой клиент имеет доступ к посту')

    def test_non_author_post_edit_redirects_correctly(self):
        """Редирект не автора поста происходит правильно"""
        form_data = {
            "text": "Тестовое создание поста"}
        response = self.authorized_non_author_client.post(
            reverse('post_edit', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }), data=form_data, follow=True
        )
        self.assertRedirects(
            response, ('/author/2/'))

    def test_server_return_404(self):
        """Несуществующая страница возвращает 404"""
        response = self.guest_client.get(
            '/exhaust/'
        )
        self.assertEqual(
            response.status_code, 404,
            'Несуществующая страница возвращает ошибочный код')

    def test_user_can_follow_and_unfollow_someone(self):
        """Подписка и отписка пользователя происходят корректно"""
        response = self.authorized_client.get(
            (reverse('profile_follow', kwargs={'username': PostURLTests.leo})))
        self.assertEqual(
            response.status_code, 302, 'Ошибка при попытке подписки'
        )
        response = self.authorized_client.get(
            (reverse('profile_unfollow', kwargs={
                'username': PostURLTests.leo})))
        self.assertEqual(
            response.status_code, 302, 'Ошибка при попытке отписки'
        )

    def test_guest_user_cant_add_comment(self):
        """Комментировать посты может только залогиненный юзер"""
        response = self.guest_client.get(
            reverse('add_comment', kwargs={
                'username': f'{self.post_author.username}',
                'post_id': f'{self.test_post.id}'
            }),
        )
        url = 'auth/login/?next=/'
        self.assertRedirects(
            response,
            f'/{url}{self.post_author.username}/{self.test_post.id}/comment/')
