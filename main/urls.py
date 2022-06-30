from django.urls import path

from . import views

urlpatterns = [
    path('ajax/load_clients', views.get_clients, name='ajax_load_clients'),

    path('', views.LawyerCasesView.as_view(), name='home'),
    path('add_case/', views.LawyerCaseCreate.as_view(), name='add_case'),
    path('delete_case/', views.LawyerCaseDelete.as_view(), name='delete_case'),
    path('close_case/<int:case_id>', views.LawyerCaseCloseUpdate.as_view(), name='close_case'),
    path('edit_case/<int:case_id>', views.LawyerCaseUpdate.as_view(), name='edit_case'),
    path('cancel_case/', views.LawyerCaseCancel.as_view(), name='cancel_case'),
    path('case/', views.LawyerCaseView.as_view(), name='show_case_info'),
    path('case_file/<int:case_id>', views.DownloadCaseFile.as_view(), name='download_case'),
    path('case_approve_file/<int:case_id>', views.DownloadCaseApproveFile.as_view(), name='download_case_approve'),

    path('add_bill/', views.AddBill.as_view(), name='add_bill'),

    path('add_client', views.AddLawyerClient.as_view(), name='add_lawyer_client')
]
