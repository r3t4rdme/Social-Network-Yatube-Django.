from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class GroupModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_group = Group.objects.create(
            title='lev_nikolaevich',
            slug='lev_nikolaevich',
            description='O lve nikolaeviche'
        )

    def test_group_str(self):
        """Метод __str__ возвращает название группы"""
        test_group = GroupModelTest.test_group
        str_title = test_group.__str__()
        self.assertEqual(test_group.title, str_title, 'Ошибка метода str')


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.leo = User.objects.create(username='leo')
        cls.test_post = Post.objects.create(
            text='This is a test post text',
            author=cls.leo
        )

    def test_post_str(self):
        """Метод ___str__ возращает первых 15 символов поста"""
        test_post_text = PostModelTest.test_post.text
        test_post = PostModelTest.test_post
        self.assertEqual(test_post_text[:15], test_post.__str__())
