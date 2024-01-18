from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Q, Count
from .models import Capsule, Tag, Category
from .forms import CapsuleForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
import json
import spacy
import random
from sklearn.feature_extraction.text import CountVectorizer
from transformers import pipeline
from textblob import TextBlob
from collections import Counter

nlp = spacy.load('en_core_web_sm')

def generate_summary(text):
    summarizer = pipeline('summarization', model='sshleifer/distilbart-cnn-12-6')
    summary = summarizer(text, max_length=90, min_length=50, do_sample=False)
    print(summary[0]['summary_text'])
    return summary[0]['summary_text']

def generate_tags(text, current_tags):
    doc = nlp(text)

    words = [token.lemma_ for token in doc if not token.is_stop and token.lemma_ not in current_tags]

    if not words:
        return []

    vectorizer = CountVectorizer().fit(words)
    bag_of_words = vectorizer.transform(words)
    sum_words = bag_of_words.sum(axis=0) 
    words_freq = [(word, sum_words[0, idx]) for word, idx in vectorizer.vocabulary_.items()]
    words_freq = sorted(words_freq, key = lambda x: x[1], reverse=True)
    
    top_words = [word for word, freq in words_freq[:8]]
    random.shuffle(top_words)
    return top_words[:5]


@login_required
def analytics_view(request):
    capsules = Capsule.objects.filter(user=request.user)

    # Total number of capsules
    total_capsules = capsules.count()

    # Number of capsules per category
    category_data = capsules.exclude(categories__isnull=True).values('categories__name').annotate(count=Count('categories')).values_list('categories__name', 'count')

    # Most common tags
    tag_data = capsules.values('tags__name').annotate(count=Count('tags')).order_by('-count').values_list('tags__name', 'count')[:8]

    # Sentiment analysis
    sentiments = [TextBlob(capsule.content).sentiment.polarity for capsule in capsules]
    average_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    # Sentiment distribution
    sentiment_distribution = Counter(
        "Positive" if sentiment > 0 else "Negative" if sentiment < 0 else "Neutral"
        for sentiment in sentiments
    )
    sentiment_data = list(sentiment_distribution.items())

    # Tag prediction
    predicted_tags = [tag for tag, _ in tag_data[:5]]

    # Number of capsules over time
    capsules_dates = [capsule.created_at.date() for capsule in capsules]
    time_distribution = Counter(capsules_dates)
    time_data = sorted(list(time_distribution.items()))
    time_data = [[str(date), count] for date, count in time_data]

    # Most common category
    most_common_category = capsules.values('categories__name').annotate(count=Count('categories')).order_by('-count').values_list('categories__name', flat=True).first()

    return render(request, 'capsules/analytics.html', {
        'total_capsules': total_capsules,
        'average_sentiment': average_sentiment,
        'predicted_tags': predicted_tags,
        'category_data': json.dumps(list(category_data)),
        'tag_data': json.dumps(list(tag_data)),
        'sentiment_data': json.dumps(sentiment_data),
        'time_data': json.dumps(time_data),
        'most_common_category': most_common_category,
    })

@login_required
def categories_view(request, cid):
    capsules = Capsule.objects.filter(categories__id__in=[cid], user=request.user).order_by('-created_at')
    return render(request, 'capsules/category.html', {'capsules': capsules, 'category': Category.objects.get(id=cid).name})

@login_required
def my_capsules(request):
    capsules = Capsule.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'capsules/my_capsules.html', {
        'capsules': capsules
        })

def summarize_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text')
        if not text:
            return JsonResponse({'error': 'No text provided'}, status=400)
        summary = generate_summary(text)
        return JsonResponse({'summary': summary})
    else:
        return JsonResponse({'error': 'Invalid request method'}, status=400)
    
def generate_tags_view(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        text = data.get('text', '')
        current_tags = data.get('current_tags', [])
        tags = generate_tags(text, current_tags)
        return JsonResponse({'tags': tags})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)

@login_required
def search(request):
    query = request.GET.get('q')
    capsules = Capsule.objects.filter(Q(content__icontains=query) | Q(tags__name__icontains=query), user=request.user).distinct().order_by('-created_at')
    return render(request, 'capsules/search_results.html', {'capsules': capsules, "searchTxt": query})

@login_required
def tag_detail(request, pk):
    tag = get_object_or_404(Tag, pk=pk)
    return render(request, 'capsules/tag_detail.html', {'tag': tag, 'capsules': tag.capsule_set.filter(user=request.user)})

@login_required
def create_capsule(request):
    if request.method == 'POST':
        form = CapsuleForm(request.POST)
        if form.is_valid():
            capsule = form.save(commit=False)
            capsule.user = request.user
            capsule.save()
            form.save_m2m()  
            return redirect('home')
    else:
        form = CapsuleForm()
    return render(request, 'capsules/create_capsule.html', {'form': form})

@login_required
def home(request):
    capsules = Capsule.objects.filter(user=request.user)
    total_capsules = capsules.count()

    tag_data = capsules.values('tags__name').annotate(count=Count('tags')).order_by('-count').values_list('tags__name', 'count')[:8]
    predicted_tags = [tag for tag, _ in tag_data[:5]]

    sentiments = [TextBlob(capsule.content).sentiment.polarity for capsule in capsules]
    average_sentiment = sum(sentiments) / len(sentiments) if sentiments else 0

    most_common_category = capsules.values('categories__name').annotate(count=Count('categories')).order_by('-count').values_list('categories__name', flat=True).first()

    recommended_capsules = Capsule.objects.filter(tags__name__in=predicted_tags, user=request.user).distinct()[:5]
    
    return render(request, 'capsules/home.html', {
        'capsules': recommended_capsules,
        'total_capsules': total_capsules,
        'average_sentiment': average_sentiment,
        'predicted_tags': predicted_tags,
        'most_common_category': most_common_category,
    })

@login_required
def capsule_detail(request, pk):
    capsule = get_object_or_404(Capsule, pk=pk, user=request.user)
    categories = capsule.categories.all()
    related_capsules = Capsule.objects.filter(
        Q(tags__in=capsule.tags.all()) | Q(categories__in=categories),
        user=request.user
    ).exclude(pk=pk).annotate(shared_tags=Count('tags')).order_by('-shared_tags')[:5]
    
    return render(request, 'capsules/capsule_detail.html', {'capsule': capsule, 'capsules': related_capsules, 'categories': categories})

@login_required
def edit_capsule(request, pk):
    capsule = get_object_or_404(Capsule, pk=pk, user=request.user)
    if request.method == 'POST':
        form = CapsuleForm(request.POST, instance=capsule)
        if form.is_valid():
            capsule = form.save()
            return redirect('capsule_detail', pk=capsule.pk)
    else:
        form = CapsuleForm(instance=capsule)
    return render(request, 'capsules/edit_capsule.html', {'form': form})

@login_required
def delete_capsule(request, pk):
    capsule = get_object_or_404(Capsule, pk=pk, user=request.user)
    if request.method == 'POST':
        capsule.delete()
        return redirect('home')
    return render(request, 'capsules/confirm_delete.html', {'capsule': capsule})