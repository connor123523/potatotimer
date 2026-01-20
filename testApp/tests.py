from django.test import TestCase
from django.contrib.auth.models import User
from .models import Post


# -------------------------
# Simple Test（简单加法测试）
# -------------------------
class SimpleTest(TestCase):
    def test_addition(self):
        a = 1
        b = 2
        result = a + b
        self.assertEqual(result, 3)


# -------------------------
# Post Model Test（模型测试）
# -------------------------
class PostModelTest(TestCase):

    def setUp(self):
        # Arrange（準備）
        self.user1 = User.objects.create_user(username='alice', password='pass')
        self.user2 = User.objects.create_user(username='bob', password='pass')

        self.post = Post.objects.create(
            author=self.user1,
            content='This is a test post content for unit test.'
        )

        self.post.likes.add(self.user1, self.user2)

    def test_str_representation(self):
        # Act & Assert
        expected = f"{self.user1.username}: {self.post.content[:20]}"
        self.assertEqual(str(self.post), expected)

    def test_total_likes(self):
        # いいね数が 2 のはず
        self.assertEqual(self.post.total_likes(), 2)

