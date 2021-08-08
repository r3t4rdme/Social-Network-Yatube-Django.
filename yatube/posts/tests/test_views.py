from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..forms import PostForm
from ..models import Group, Post

User = get_user_model()


class PostsViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leo = User.objects.create(username='leo')
        cls.Vasya = User.objects.create(username='Vasya')
        cls.test_group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test group for test'
        )
        cls.test_group_two = Group.objects.create(
            title='test group #2',
            slug='test-slug-two',
            description='test group #2 for test'
        )

        cls.test_post = Post.objects.create(
            text='test post',
            author=cls.leo,
            group=cls.test_group
        )
        cls.test_post_two = Post.objects.create(
            text='test post group two',
            author=cls.leo,
            group=cls.test_group_two
        )
        cls.test_post_three = Post.objects.create(
            text='test post group three',
            author=cls.Vasya,
            group=cls.test_group_two
        )
        cls.author_client = Client()
        cls.author_client.force_login(cls.leo)
        cls.vasya_client = Client()
        cls.vasya_client.force_login(cls.Vasya)

    def setUp(self):
        self.user = User.objects.create_user(username='peter')
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.posts_urls = {
            'posts/index.html': reverse('index'),
            'posts/new.html': reverse('new_post'),
            'posts/group.html': (
                reverse('group_posts', kwargs={
                    'slug': f'{PostsViewTests.test_group.slug}'})
            ),
        }
        cache.clear()

    def test_urls_uses_correct_template(self):
        """View-функция вызывает соответствующий шаблон"""
        for template, reverse_name in self.posts_urls.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом"""
        response = self.authorized_client.get(reverse('index'))
        first_object = response.context.get('page').object_list[1]
        post_text = first_object.text
        post_author = first_object.author.username
        self.assertEqual(
            post_text, 'test post group two', 'post text value failure')
        self.assertEqual(
            post_author, 'leo', 'post author value failure')

    def test_group_posts_show_correct_context(self):
        """Шаблон group_posts сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('group_posts', kwargs={
                'slug': f'{PostsViewTests.test_group.slug}'}))
        first_object = response.context.get('page').object_list[0]
        post_text = first_object.text
        post_author = first_object.author.username
        post_group = first_object.group.title
        self.assertEqual(post_text, 'test post', 'post text value failure')
        self.assertEqual(post_author, 'leo', 'post author value failure')
        self.assertEqual(post_group, 'test group', 'post group value failure')

    def test_new_post_show_correct_context(self):
        response = self.authorized_client.get(reverse('new_post'))
        form = response.context['form']
        self.assertIsInstance(form, PostForm, 'Form value error')

    def test_post_edit_show_correct_context(self):
        response = self.author_client.get(
            reverse('post_edit', kwargs={
                'username': PostsViewTests.leo,
                'post_id': PostsViewTests.test_post.id
            }),
        )
        form = response.context['form']
        self.assertIsInstance(form, PostForm, 'Form value error')

    def test_profile_context_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом"""
        response = self.authorized_client.get(
            reverse('profile', kwargs={
                'username': PostsViewTests.leo
            }),
        )
        response_objects = response.context.get('posts')
        for posts in response_objects:
            with self.subTest(posts=posts):
                self.assertEqual(
                    posts.author.username,
                    'leo', 'На странице профиля отображаются чужие посты')

    def test_post_show_correct_context(self):
        """Страница одиночного поста отображает 1 пост"""
        response = self.authorized_client.get(
            reverse('post', kwargs={
                'username': PostsViewTests.leo,
                'post_id': PostsViewTests.test_post_two.id
            })
        )
        first_object = response.context.get('post')
        post_text = first_object.text
        post_author = first_object.author.username
        self.assertEqual(
            post_text, 'test post group two',
            'Контекст некорректен')
        self.assertEqual(
            post_author, 'leo', 'Контекст отображается некоректно')

    def test_new_post_placed_correctly(self):
        """Новый пост появляется в соответствующих местах"""
        response_index = self.guest_client.get(reverse('index'))
        response_group = self.guest_client.get(reverse(
            'group_posts', kwargs={
                'slug': f'{PostsViewTests.test_group.slug}'}))
        response_group_two = self.guest_client.get(reverse(
            'group_posts', kwargs={
                'slug': f'{PostsViewTests.test_group_two.slug}'}))

        index_post = response_index.context.get(
            'page').object_list[0]
        test_group_post = response_group.context.get(
            'page').object_list[0]
        test_group_two_post = response_group_two.context.get(
            'page').object_list[0]

        index_post_text = index_post.text
        test_group_post_text = test_group_post.text
        test_group_two_post_text = test_group_two_post.text

        self.assertIn(
            'test post group three',
            index_post_text, 'Пост не появляется на главной странице')
        self.assertIn(
            index_post_text,
            test_group_two_post_text, 'Пост не появляется на странице группы')
        self.assertNotIn(
            index_post_text,
            test_group_post_text, 'Пост появляется не в той группе')

    def test_followers_post_placed_correctly(self):
        vasya_follow_leo = self.vasya_client.get(
            (reverse(
                'profile_follow', kwargs={'username': PostsViewTests.leo})))
        leo_post = Post.objects.create(
            author=PostsViewTests.leo, text='post for vasya')
        response = self.vasya_client.get(
            reverse('follow_index'))
        response_post = response.context['page'][0].text
        self.assertEqual(
            vasya_follow_leo.status_code,
            HTTPStatus.FOUND.value, 'Подписки не происходит')
        self.assertEqual(
            response_post,
            leo_post.text, 'Пост из подписок в ленте не появляется')

    def test_index_cache_exist(self):
        """Главная страница корректно кэшируется"""
        response = self.author_client.get(
            reverse('index')
        )
        test_object = response.context.get('page').object_list[1]
        Post.objects.get(id=2).delete()
        test_object_two = response.context.get('page').object_list[1]
        self.assertEqual(
            test_object, test_object_two, 'Проблемы с кэшем главной страницы'
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leo = User.objects.create(username='leo')
        cls.test_group = Group.objects.create(
            title='test group',
            slug='test-slug',
            description='test group for test'
        )
        for i in range(12):
            Post.objects.create(
                text=f'test post #{i}',
                author=cls.leo,
                group=cls.test_group,
            )
        cls.test_post_one = Post.objects.create(
            text='test post',
            author=cls.leo,
            group=cls.test_group
        )

    def setUp(self):
        self.client = Client()
        cache.clear()

    def test_first_page_contains_ten_records(self):
        """Paginator выводит заданное количество постов"""
        response = self.client.get(reverse('index'))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_second_page_contains_three_records(self):
        response = self.client.get(reverse('index') + '?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_group_first_page_contains_twelve_records(self):
        """Paginator группы выводит заданное количество постов"""
        response = self.client.get(reverse(
            'group_posts', kwargs={
                'slug': f'{PaginatorViewsTest.test_group.slug}'}))
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_group_second_page_contains_one_record(self):
        """Paginator группы выводит заданное количество постов"""
        response = self.client.get(
            f'/group/{PaginatorViewsTest.test_group.slug}/?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)

    def test_profile_first_page_contains_10_records(self):
        """Paginator профайла выводит заданное количество постов"""
        response = self.client.get(f'/{PaginatorViewsTest.leo.username}/')
        self.assertEqual(len(response.context.get('page').object_list), 10)

    def test_profile_second_page_contains_2_records(self):
        """Paginator профайла выводит заданное количество постов"""
        response = self.client.get(
            f'/{PaginatorViewsTest.leo.username}/?page=2')
        self.assertEqual(len(response.context.get('page').object_list), 3)
