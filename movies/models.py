from django.db import models
from django.contrib.auth.models import User

class Movie(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to='movie_images/')

    def __str__(self):
        return str(self.id) + ' - ' + self.name

class Review(models.Model):
    id = models.AutoField(primary_key=True)
    comment = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_removed = models.BooleanField(
        default=False,
        help_text="Check this box if the review is inappropriate. It will be hidden from the movie page.",
    )

    def __str__(self):
        return str(self.id) + ' - ' + self.movie.name

class ReviewFlag(models.Model):
    SUGGEST_REMOVAL = 'removal suggestion'
    MODERATOR_DELETION = 'moderator deletion'

    id = models.AutoField(primary_key=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='review_flags')
    review = models.ForeignKey(Review, on_delete=models.CASCADE, related_name='flags')
    flag = models.CharField(max_length=30, db_index=True, default=SUGGEST_REMOVAL)
    flag_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [('user', 'review', 'flag')]

    def __str__(self):
        return self.flag + ' - review ' + str(self.review.id) + ' by ' + self.user.username