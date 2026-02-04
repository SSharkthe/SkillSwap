from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.contenttypes.models import ContentType
from django.db import IntegrityError
from django.db.models import Avg, Count, F, Max, Prefetch, Q
from django.http import Http404, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import NoReverseMatch, reverse_lazy
from django.utils.decorators import method_decorator
from django.views.generic import DetailView, ListView, TemplateView, UpdateView

from .forms import FeedbackForm, MatchInviteForm, MessageForm, ProfileForm, RegistrationForm, ReportForm, RequestForm, \
    UserSkillForm

from .models import (
    Block,
    Conversation,
    Feedback,
    Match,
    Message,
    Notification,
    Profile,
    Report,
    Request,
    Skill,
    UserSkill,
    blocked_user_ids,
    is_blocked,
)

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
        context['offers'] = self.object.user.user_skills.filter(type=UserSkill.SkillType.OFFER).select_related('skill')
        context['wants'] = self.object.user.user_skills.filter(type=UserSkill.SkillType.WANT).select_related('skill')
        context['is_blocked'] = is_blocked(self.request.user, self.object.user)
        context['has_blocked'] = Block.objects.filter(
            blocker=self.request.user,
            blocked=self.object.user,
        ).exists()
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
def block_toggle(request, username):
    if request.method != 'POST':
        return HttpResponseForbidden('Invalid method.')
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return HttpResponseForbidden('Cannot block yourself.')
    block, created = Block.objects.get_or_create(blocker=request.user, blocked=target)
    if created:
        messages.success(request, 'User blocked.')
    else:
        block.delete()
        messages.success(request, 'User unblocked.')
    next_url = request.POST.get('next') or request.GET.get('next') or target.profile.get_absolute_url()
    return redirect(next_url)


@login_required
def blocked_list(request):
    blocked_users = User.objects.filter(blocked_by__blocker=request.user).select_related('profile')
    return render(request, 'skillswap/blocked_list.html', {'blocked_users': blocked_users})


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
            user_skill.profile = request.user.profile
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
            updated_skill = form.save(commit=False)
            updated_skill.profile = request.user.profile
            updated_skill.save()
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
        context['is_bookmarked'] = self.request.user.profile.bookmarked_requests.filter(pk=req.pk).exists()
        context['is_blocked'] = is_blocked(self.request.user, req.user)
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
            blocked_ids = blocked_user_ids(self.request.user)
            if blocked_ids:
                queryset = queryset.exclude(user__in=blocked_ids)
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


@login_required
def bookmark_toggle(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden('Invalid method.')
    request_obj = get_object_or_404(Request, pk=pk)
    profile = request.user.profile
    if profile.bookmarked_requests.filter(pk=request_obj.pk).exists():
        profile.bookmarked_requests.remove(request_obj)
        messages.info(request, 'Removed from bookmarks.')
    else:
        profile.bookmarked_requests.add(request_obj)
        messages.success(request, 'Bookmarked.')
    next_url = request.POST.get('next') or request.GET.get('next') or request_obj.get_absolute_url()
    return redirect(next_url)


@login_required
def bookmark_list(request):
    bookmarks = request.user.profile.bookmarked_requests.select_related('skill', 'user').order_by('-created_at')
    return render(request, 'skillswap/bookmarks.html', {'bookmarks': bookmarks})


@login_required
def notification_list(request):
    notifications = request.user.notifications.select_related('actor', 'match', 'request')
    return render(request, 'skillswap/notifications.html', {'notifications': notifications})


@login_required
def notification_mark_read(request, pk):
    if request.method != 'POST':
        return HttpResponseForbidden('Invalid method.')
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    if not notification.is_read:
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        messages.success(request, 'Notification marked as read.')
    return redirect('skillswap:notifications')

@login_required
def inbox_list(request):
    user = request.user
    matches = Match.objects.filter(
        Q(requester=user) | Q(partner=user),
        status__in=[Match.Status.ACCEPTED, Match.Status.COMPLETED],
    )
    for match in matches:
        Conversation.objects.get_or_create(match=match)
    conversations = (
        Conversation.objects.filter(
            Q(match__requester=user) | Q(match__partner=user),
            match__status__in=[Match.Status.ACCEPTED, Match.Status.COMPLETED],
        )
        .select_related('match', 'match__request', 'match__requester', 'match__partner')
        .annotate(
            last_message_at=Max('messages__created_at'),
            unread_count=Count('messages', filter=Q(messages__is_read=False) & ~Q(messages__sender=user)),
        )
        .order_by('-last_message_at', '-created_at')
    )
    for conversation in conversations:
        conversation.last_message = conversation.messages.order_by('-created_at').first()
        conversation.counterpart = (
            conversation.match.partner
            if conversation.match.requester == user
            else conversation.match.requester
        )
    return render(request, 'skillswap/inbox_list.html', {'conversations': conversations})


@login_required
def inbox_detail(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.user not in {match.requester, match.partner}:
        return HttpResponseForbidden('Not allowed.')
    if match.status not in {Match.Status.ACCEPTED, Match.Status.COMPLETED}:
        return HttpResponseForbidden('Conversation not available.')
    conversation, _ = Conversation.objects.get_or_create(match=match)
    counterpart = match.partner if request.user == match.requester else match.requester
    is_blocked_flag = is_blocked(request.user, counterpart)
    Message.objects.filter(conversation=conversation, sender=counterpart, is_read=False).update(is_read=True)
    message_form = MessageForm()
    conversation_messages = conversation.messages.select_related('sender')
    return render(
        request,
        'skillswap/inbox_detail.html',
        {
            'match': match,
            'conversation': conversation,
            'conversation_messages': conversation_messages,
            'message_form': message_form,
            'counterpart': counterpart,
            'is_blocked': is_blocked_flag,
        },
    )


@login_required
def inbox_send(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    if request.user not in {match.requester, match.partner}:
        return HttpResponseForbidden('Not allowed.')
    if match.status not in {Match.Status.ACCEPTED, Match.Status.COMPLETED}:
        return HttpResponseForbidden('Conversation not available.')
    counterpart = match.partner if request.user == match.requester else match.requester
    if is_blocked(request.user, counterpart):
        return HttpResponseForbidden('Messaging is blocked.')
    if request.method != 'POST':
        return HttpResponseForbidden('Invalid method.')
    conversation, _ = Conversation.objects.get_or_create(match=match)
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        messages.success(request, 'Message sent.')
    else:
        messages.error(request, 'Please enter a message.')
    return redirect('skillswap:inbox-detail', match_id=match.pk)



class ExploreUserListView(LoginRequiredMixin, ListView):
    template_name = 'skillswap/explore_users.html'
    context_object_name = 'users'
    paginate_by = 12

    def get_queryset(self):
        queryset = User.objects.select_related('profile').all()
        if self.request.user.is_authenticated:
            queryset = queryset.exclude(pk=self.request.user.pk)
            blocked_ids = blocked_user_ids(self.request.user)
            if blocked_ids:
                queryset = queryset.exclude(pk__in=blocked_ids)
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
    if is_blocked(request.user, req.user):
        return HttpResponseForbidden('Cannot send a match invite to this user.')
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
        context['is_blocked'] = is_blocked(match.requester, match.partner)
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
def report_form(request):
    ct_id = request.GET.get('ct')
    obj_id = request.GET.get('oid')
    if not ct_id or not obj_id:
        raise Http404
    content_type = get_object_or_404(ContentType, pk=ct_id)
    model_class = content_type.model_class()
    if model_class is None:
        raise Http404
    target = get_object_or_404(model_class, pk=obj_id)
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.reporter = request.user
            report.content_type = content_type
            report.object_id = target.pk
            report.reported_user = _infer_reported_user(target)
            report.save()
            messages.success(request, 'Report submitted. Thank you for helping keep SkillSwap safe.')
            next_url = request.POST.get('next') or request.GET.get('next') or _safe_target_url(target)
            return redirect(next_url)
    else:
        form = ReportForm()
    return render(
        request,
        'skillswap/report_form.html',
        {
            'form': form,
            'content_type': content_type,
            'target': target,
        },
    )


@login_required
def report_request(request, pk):
    req = get_object_or_404(Request, pk=pk)
    ct = ContentType.objects.get_for_model(Request)
    return redirect(f"{reverse_lazy('skillswap:report')}?ct={ct.pk}&oid={req.pk}")


@login_required
def report_profile(request, username):
    profile = get_object_or_404(Profile, user__username=username)
    ct = ContentType.objects.get_for_model(Profile)
    return redirect(f"{reverse_lazy('skillswap:report')}?ct={ct.pk}&oid={profile.pk}")


@login_required
def report_message(request, pk):
    message = get_object_or_404(Message, pk=pk)
    ct = ContentType.objects.get_for_model(Message)
    return redirect(f"{reverse_lazy('skillswap:report')}?ct={ct.pk}&oid={message.pk}")


@login_required
def my_reports(request):
    reports = Report.objects.filter(reporter=request.user).select_related('reported_user', 'content_type')
    return render(request, 'skillswap/my_reports.html', {'reports': reports})


@user_passes_test(lambda u: u.is_staff)
def moderation_reports(request):
    reports = Report.objects.filter(status__in=[Report.Status.OPEN, Report.Status.REVIEWING]).select_related(
        'reporter',
        'reported_user',
        'content_type',
    )
    return render(request, 'skillswap/mod_reports.html', {'reports': reports})



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
        return HttpResponse('Invalid method.')
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

def _infer_reported_user(target):
    if isinstance(target, Profile):
        return target.user
    if isinstance(target, Request):
        return target.user
    if isinstance(target, Message):
        return target.sender
    if hasattr(target, "user"):
        return target.user
    return None


def _safe_target_url(target):
    if hasattr(target, "get_absolute_url"):
        try:
            return target.get_absolute_url()
        except NoReverseMatch:
            return reverse_lazy("skillswap:dashboard")
    return reverse_lazy("skillswap:dashboard")



def get_recommended_partners(user, q=None, mode=None, limit=None):
    want_skills = UserSkill.objects.filter(user=user, type=UserSkill.SkillType.WANT)
    if q:
        want_skills = want_skills.filter(skill__name__icontains=q)
    want_skill_ids = list(want_skills.values_list('skill_id', flat=True))
    if not want_skill_ids:
        return User.objects.none()

    offer_skill_ids = list(
        UserSkill.objects.filter(user=user, type=UserSkill.SkillType.OFFER).values_list('skill_id', flat=True)
    )

    qs = User.objects.select_related('profile').exclude(pk=user.pk)
    blocked_ids = blocked_user_ids(user)
    if blocked_ids:
        qs = qs.exclude(pk__in=blocked_ids)
    if mode in {choice[0] for choice in Profile.PreferredMode.choices}:
        qs = qs.filter(profile__preferred_mode=mode)
    qs = qs.annotate(
        overlap_want_offer=Count(
            'user_skills__skill',
            filter=Q(
                user_skills__type=UserSkill.SkillType.OFFER,
                user_skills__skill_id__in=want_skill_ids,
            ),
            distinct=True,
        ),
        mutual_overlap=Count(
            'user_skills__skill',
            filter=Q(
                user_skills__type=UserSkill.SkillType.WANT,
                user_skills__skill_id__in=offer_skill_ids,
            ),
            distinct=True,
        ),
    ).filter(overlap_want_offer__gt=0)

    qs = qs.annotate(
        final_score=F('overlap_want_offer') + F('mutual_overlap'),
    )

    qs = qs.prefetch_related(
        Prefetch(
            'user_skills',
            queryset=UserSkill.objects.filter(
                type=UserSkill.SkillType.OFFER,
                skill_id__in=want_skill_ids,
            ).select_related('skill'),
            to_attr='matching_offers',
        ),
    ).order_by('-final_score', '-overlap_want_offer', 'username')

    if limit:
        return qs[:limit]
    return qs
