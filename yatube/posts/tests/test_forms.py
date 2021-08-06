import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        settings.MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)
        cls.leo = User.objects.create(username='leo')
        cls.test_group = Group.objects.create(
            title='Test Group',
            slug='test-slug',
            description='Test group for test'
        )
        cls.test_post = Post.objects.create(
            text='Тестовый текст',
            author=cls.leo,
            group=cls.test_group
        )
        cls.post_author_client = Client()
        cls.post_author_client.force_login(cls.leo)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(settings.MEDIA_ROOT, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        self.petr = User.objects.create_user(username='petr')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.petr)

    def test_new_post_created(self):
        posts_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        form_data = {
            'text': 'Текст из формы',
            'group': PostCreateFormTests.test_group.id,
            'image': uploaded,
        }
        response = PostCreateFormTests.post_author_client.post(
            reverse('new_post'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response, reverse('index'))
        self.assertEqual(
            Post.objects.count(), posts_count + 1)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=PostCreateFormTests.leo,
                group=PostCreateFormTests.test_group,
                image='posts/small.gif'
            ),
        )

    def test_post_edited(self):
        form_data = {
            'text': 'Измененный текст',
        }
        editing = self.post_author_client.post(
            reverse('post_edit', kwargs={
                'username': PostCreateFormTests.leo,
                'post_id': PostCreateFormTests.test_post.id
            }),
            data=form_data,
            follow=True
        )
        after_edit_response = self.post_author_client.get(
            reverse('post', kwargs={
                'username': PostCreateFormTests.leo,
                'post_id': PostCreateFormTests.test_post.id
            }),
        )
        work_post = after_edit_response.context.get('post')
        work_post_text = work_post.text
        self.assertRedirects(
            editing,
            f'/{PostCreateFormTests.leo.username}'
            f'/{PostCreateFormTests.test_post.id}/')
        self.assertEqual(
            work_post_text,
            'Измененный текст', 'Текст поста не изменился')
