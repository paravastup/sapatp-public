class AuditMiddleware:
	def __init__(self, get_response):
		self.get_response = get_response
		
	def __call__(self, request):
		if request.user.is_authenticated:
			# Get the AuditEntry object for the current session and user
			audit_entry, created = AuditEntry.objects.get_or_create(session_key=request.session.session_key, user=request.user.id, defaults={'host': request.META['HTTP_HOST'], 'ip': request.get_host()})
				# Update the login time if the object was just created
			if created:
				audit_entry.login_time = datetime.datetime.now()
				audit_entry.save()
				# Update the logout time if the user is logging out
			if request.path == '/accounts/logout/':
				audit_entry.logout_time = datetime.datetime.now()
				audit_entry.save()
				response = self.get_response(request)
				return response
