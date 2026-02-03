from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.db.models import Avg, Case, Count, IntegerField, Prefetch, Q, Value, When
from django.http import Http404, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from .forms import FeedbackForm, MatchInviteForm, ProfileForm, RegistrationForm, RequestForm, UserSkillForm
from .models import Feedback, Match, Profile, Request, Skill, UserSkill

User = get_user_model()


class HomeView(TemplateView):
    template_name = 'skillswap/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['recent_requests'] = Request.objects.select_related('skill', 'user')[:3]
        context['skill_count'] = Skill.objects.count()
        context['member_count'] = User.objects.count()
        return context


def register_view(request):
    if request.user.is_authenticated:
        return redirect('skillswap:dashboard')

    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Welcome to SkillSwap! Complete your profile to get started.')
            return redirect('skillswap:dashboard')
    else:
        form = RegistrationForm()

    return render(request, 'registration/register.html', {'form': form})


@method_decorator(login_required, name='dispatch')
class DashboardView(TemplateView):
    template_name = 'skillswap/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        context['profile'] = user.profile
        context['offers'] = user.user_skills.filter(type=UserSkill.SkillType.OFFER)
        context['wants'] = user.user_skills.filter(type=UserSkill.SkillType.WANT)
        context['requests'] = user.requests.select_related('skill')
        context['matches'] = Match.objects.filter(Q(requester=user) | Q(partner=user)).select_related('request')
        context['recommended_partners'] = get_recommended_partners(user=user, limit=6)
        return context


class ProfileDetailView(LoginRequiredMixin, DetailView):
    template_name = 'skillswap/profile_detail.html'
    context_object_name = 'profile'

    def get_object(self, queryset=None):
        user = get_object_or_404(User, username=self.kwargs['username'])
        return user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        rating_summary = self.object.user.received_feedback.aggregate(
            average=Avg('rating'),
            count=Count('id'),
        )
        context['rating_summary'] = rating_summary
        context['recent_feedback'] = self.object.user.received_feedback.exclude(comment='')[:3]
        return context


class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'skillswap/profile_form.html'
    success_url = reverse_lazy('skillswap:dashboard')

    def get_object(self, queryset=None):
        return self.request.user.profile

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully.')
        return super().form_valid(form)


@login_required
def my_skills_view(request):
    offers = request.user.user_skills.filter(type=UserSkill.SkillType.OFFER).select_related('skill')
    wants = request.user.user_skills.filter(type=UserSkill.SkillType.WANT).select_related('skill')
    return render(request, 'skillswap/my_skills.html', {'offers': offers, 'wants': wants})


@login_required
def user_skill_create(request):
    if request.method == 'POST':
        form = UserSkillForm(request.POST)
        if form.is_valid():
            user_skill = form.save(commit=False)
            user_skill.user = request.user
            try:
                user_skill.save()
                messages.success(request, 'Skill saved.')
                return redirect('skillswap:my-skills')
            except IntegrityError:
                form.add_error(None, 'You already added this skill with the same type.')
    else:
        form = UserSkillForm()
    return render(request, 'skillswap/user_skill_form.html', {'form': form, 'action': 'Add'})


@login_required
def user_skill_update(request, pk):
    user_skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    if request.method == 'POST':
        form = UserSkillForm(request.POST, instance=user_skill)
        if form.is_valid():
            form.save()
            messages.success(request, 'Skill updated.')
            return redirect('skillswap:my-skills')
    else:
        form = UserSkillForm(instance=user_skill)
    return render(request, 'skillswap/user_skill_form.html', {'form': form, 'action': 'Update'})


@login_required
def user_skill_delete(request, pk):
    user_skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    if request.method == 'POST':
        user_skill.delete()
        messages.success(request, 'Skill removed.')
        return redirect('skillswap:my-skills')
    return render(request, 'skillswap/user_skill_confirm_delete.html', {'user_skill': user_skill})


class MyRequestListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/my_requests.html'
    context_object_name = 'requests'

    def get_queryset(self):
        return self.request.user.requests.select_related('skill')


@login_required
def request_create(request):
    if request.method == 'POST':
        form = RequestForm(request.POST)
        if form.is_valid():
            req = form.save(commit=False)
            req.user = request.user
            req.save()
            messages.success(request, 'Request created.')
            return redirect('skillswap:my-requests')
    else:
        form = RequestForm()
    return render(request, 'skillswap/request_form.html', {'form': form, 'action': 'Create'})


@login_required
def request_update(request, pk):
    req = get_object_or_404(Request, pk=pk, user=request.user)
    if request.method == 'POST':
        form = RequestForm(request.POST, instance=req)
        if form.is_valid():
            form.save()
            messages.success(request, 'Request updated.')
            return redirect(req.get_absolute_url())
    else:
        form = RequestForm(instance=req)
    return render(request, 'skillswap/request_form.html', {'form': form, 'action': 'Update'})


class RequestDetailView(LoginRequiredMixin, DetailView):
    model = Request
    template_name = 'skillswap/request_detail.html'
    context_object_name = 'request_obj'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        req = self.object
        context['can_edit'] = req.user == self.request.user
        context['invite_form'] = MatchInviteForm()
        context['existing_match'] = Match.objects.filter(
            request=req,
            requester=self.request.user,
            partner=req.user,
            status=Match.Status.PENDING,
        ).first()
        return context


@login_required
def request_close(request, pk):
    req = get_object_or_404(Request, pk=pk, user=request.user)
    if request.method == 'POST':
        req.status = Request.Status.CLOSED
        req.save(update_fields=['status'])
        messages.success(request, 'Request closed.')
        return redirect(req.get_absolute_url())
    return render(request, 'skillswap/request_close_confirm.html', {'request_obj': req})


class ExploreRequestListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/explore_requests.html'
    context_object_name = 'requests'
    paginate_by = 10

    def get_queryset(self):
        queryset = Request.objects.select_related('skill', 'user').filter(status=Request.Status.OPEN)
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(user=self.request.user)
        q = self.request.GET.get('q')
        category = self.request.GET.get('category')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) | Q(description__icontains=q) | Q(skill__name__icontains=q))
        if category:
            queryset = queryset.filter(skill__category__icontains=category)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Skill.objects.values_list('category', flat=True).distinct()
        return context


class ExploreUserListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/explore_users.html'
    context_object_name = 'users'
    paginate_by = 12

    def get_queryset(self):
        queryset = User.objects.select_related('profile').all()
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(pk=self.request.user.pk)
        skill_query = self.request.GET.get('skill')
        skill_type = self.request.GET.get('type')
        if skill_query:
            queryset = queryset.filter(user_skills__skill__name__icontains=skill_query)
        if skill_type in {UserSkill.SkillType.OFFER, UserSkill.SkillType.WANT}:
            queryset = queryset.filter(user_skills__type=skill_type)
        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skill_type_choices'] = UserSkill.SkillType.choices
        return context


@login_required
def match_create(request, pk):
    req = get_object_or_404(Request, pk=pk)
    if req.user == request.user:
        return HttpResponseForbidden('Cannot match your own request.')
    if request.method == 'POST':
        form = MatchInviteForm(request.POST)
        if form.is_valid():
            try:
                Match.objects.create(request=req, requester=request.user, partner=req.user)
                messages.success(request, 'Invitation sent!')
            except IntegrityError:
                messages.error(request, 'An invitation is already pending.')
    return redirect(req.get_absolute_url())


class MatchListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/match_list.html'
    context_object_name = 'matches'

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(Q(requester=user) | Q(partner=user)).select_related('request')


class MatchDetailView(LoginRequiredMixin, DetailView):
    model = Match
    template_name = 'skillswap/match_detail.html'
    context_object_name = 'match'

    def get_object(self, queryset=None):
        match = super().get_object(queryset)
        if self.request.user not in {match.requester, match.partner}:
            raise Http404
        return match

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        match = self.object
        context['feedback_entries'] = match.feedback.select_related('rater', 'ratee')
        existing_feedback = match.feedback.filter(rater=self.request.user).first()
        context['existing_feedback'] = existing_feedback
        if match.status == Match.Status.COMPLETED and existing_feedback is None:
            context['feedback_form'] = FeedbackForm()
        return context


@login_required
def match_action(request, pk, action):
    match = get_object_or_404(Match, pk=pk)
    if request.user not in {match.requester, match.partner}:
        return HttpResponseForbidden('Not allowed.')

    if action in {'accept', 'reject'} and request.user != match.partner:
        return HttpResponseForbidden('Only the recipient can respond.')

    if action == 'accept' and match.status == Match.Status.PENDING:
        match.status = Match.Status.ACCEPTED
        match.save(update_fields=['status'])
        messages.success(request, 'Match accepted.')
    elif action == 'reject' and match.status == Match.Status.PENDING:
        match.status = Match.Status.REJECTED
        match.save(update_fields=['status'])
        messages.info(request, 'Match rejected.')
    elif action == 'complete' and match.status == Match.Status.ACCEPTED:
        match.status = Match.Status.COMPLETED
        match.save(update_fields=['status'])
        messages.success(request, 'Match marked completed.')
    else:
        messages.warning(request, 'Action not available.')

    return redirect(match.get_absolute_url())


class RecommendationListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/recommendations.html'
    context_object_name = 'recommendations'

    def get_queryset(self):
        return get_recommended_partners(
            user=self.request.user,
            q=self.request.GET.get('q'),
            mode=self.request.GET.get('mode'),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['mode_choices'] = Profile.PreferredMode.choices
        context['q'] = self.request.GET.get('q', '')
        context['mode'] = self.request.GET.get('mode', '')
        return context


@login_required
def feedback_create(request, pk):
    match = get_object_or_404(Match, pk=pk)
    if request.user not in {match.requester, match.partner}:
        return HttpResponseForbidden('Not allowed.')
    if match.status != Match.Status.COMPLETED:
        return HttpResponseForbidden('Match is not completed.')
    if Feedback.objects.filter(match=match, rater=request.user).exists():
        messages.info(request, 'You already left feedback for this match.')
        return redirect(match.get_absolute_url())
    if request.method != 'POST':
        return HttpResponseForbidden('Invalid method.')
    form = FeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.match = match
        feedback.rater = request.user
        feedback.ratee = match.partner if request.user == match.requester else match.requester
        feedback.save()
        messages.success(request, 'Feedback submitted. Thank you!')
    else:
        messages.error(request, 'Please correct the feedback form.')
    return redirect(match.get_absolute_url())


def get_recommended_partners(user, q=None, mode=None, limit=None):
    want_skills = UserSkill.objects.filter(user=user, type=UserSkill.SkillType.WANT)
    if q:
        want_skills = want_skills.filter(skill__name__icontains=q)
    want_skill_ids = list(want_skills.values_list('skill_id', flat=True))
    if not want_skill_ids:
        return User.objects.none()

    matched_user_ids = Match.objects.filter(
        Q(requester=user) | Q(partner=user),
        status__in=[Match.Status.ACCEPTED, Match.Status.COMPLETED],
    ).values_list('requester_id', 'partner_id')
    exclude_ids = {user.id}
    for requester_id, partner_id in matched_user_ids:
        exclude_ids.update({requester_id, partner_id})

    qs = User.objects.select_related('profile').exclude(id__in=exclude_ids)
    if mode in {choice[0] for choice in Profile.PreferredMode.choices}:
        qs = qs.filter(profile__preferred_mode=mode)
    qs = qs.annotate(
        overlap_count=Count(
            'user_skills__skill',
            filter=Q(
                user_skills__type=UserSkill.SkillType.OFFER,
                user_skills__skill_id__in=want_skill_ids,
            ),
            distinct=True,
        ),
        completeness=Case(
            When(
                ~Q(profile__bio='') & ~Q(profile__availability=''),
                then=Value(2),
            ),
            When(
                ~Q(profile__bio='') | ~Q(profile__availability=''),
                then=Value(1),
            ),
            default=Value(0),
            output_field=IntegerField(),
        ),
    ).filter(overlap_count__gt=0)

    qs = qs.prefetch_related(
        Prefetch(
            'user_skills',
            queryset=UserSkill.objects.filter(
                type=UserSkill.SkillType.OFFER,
                skill_id__in=want_skill_ids,
            ).select_related('skill'),
            to_attr='matching_offers',
        ),
    ).order_by('-overlap_count', '-completeness', 'username')

    if limit:
        return qs[:limit]
    return qs
