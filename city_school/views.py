import requests
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
import barcode
from barcode.writer import ImageWriter
import base64
import json
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from barcode import Code128


# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)


##################################### Log In Page ##################################################################
def Login(request):
    if request.method == "GET":
        if 'mobile_number' in request.session:
            return redirect('dashboard') 
        else:
            return render(request, 'city_school/login.html')
    elif request.method == "POST":
        # Get mobile number from POST data
        mobile_number = request.POST.get('mobileNumber')
        # print("Mobile Number:", mobile_number)
        
        
        
        # Disable SSL certificate verification (for development purposes)
        requests.packages.urllib3.disable_warnings()
        
        # Call the first API with the mobile number
        api_url = "https://mispack.in/app/admin/public/checkNumber"
        api_data = {"mobile": mobile_number}
        response = requests.post(api_url, json=api_data, verify=False)
        
        # Check if the request was successful
        if response.status_code == 200:
            # Check if the response is true
            if response.json().get('response') == True:
                # Call the second API to send OTP
                otp_api_url = "https://mispack.in/app/admin/public/otp"
                otp_data = {
                    "mobile_no": mobile_number,
                    "gcm_id": 1,
                    "ios_id": 0
                }
                otp_response = requests.post(otp_api_url, json=otp_data, verify=False)
                # Store mobile number in session
                request.session['mobile_number'] = mobile_number
                return redirect('otp')  # Assuming 'otp' is the name of your OTP view
            
            else:
                # If the response is not true, add an error message
                messages.add_message(request, messages.ERROR, "Mobile number not found")
                return redirect('login')  # Assuming 'login' is the name of your login view
        else:
            # If the first API request was unsuccessful, add an error message
            messages.add_message(request, messages.ERROR, "Error: Unable to fetch data from the API")
            return redirect('login')  # Assuming 'login' is the name of your login view

##################################### OTP Page ##################################################################

def Otp(request):
    if request.method == "GET":
        return render(request, 'city_school/otp.html')
    else:
        mobile_number = request.session.get('mobile_number')
        # print("Mobile Number in OTP:", mobile_number)
        
        otp = request.POST.get('otp')
        # print("OTP:", otp)
        
        # Make a POST request to the loginmobile API
        api_url = "https://mispack.in/app/admin/public/loginmobile"
        api_data = {
            "mobile": mobile_number,
            "otp": otp
        }
        
        # Disable SSL certificate verification (for development purposes)
        requests.packages.urllib3.disable_warnings()
        
        # Call the loginmobile API
        response = requests.post(api_url, json=api_data, verify=False)
        
        # Print API response to terminal
        
        # print("API Response:", response.text)
        
        output=response.json()
        # print(output)
        
        # return HttpResponse(output)
    
        # Check if the request was successful
        if output["response"]:
            # Assuming successful login redirects to dashboard
             # Store mobile number in session
            request.session['output'] = output
            # print(request.session['output'])
            return redirect('my_students')  # Assuming 'dashboard' is the name of your dashboard view
        else:
            # If the login request was unsuccessful, return an error response
            messages.success(request, "Otp is not valid")
            return redirect('otp')

##################################### Dashboard Page ##################################################################
def DashboardPage(request):
    # Retrieve the selected admin numbers from the session
    selected_admin_numbers = request.session.get('selected_admin_numbers', [])
    
    # Retrieve the mobile number from the session
    mobile_number = request.session.get('mobile_number')
    
    # API endpoint URL for student data
    student_api_url = 'https://mispack.in/app/admin/public/getAllStudent'
    student_api_data = {'mobile': mobile_number}
    
    try:
        # Make API request to get student data
        student_response = requests.post(student_api_url, json=student_api_data, verify=False)
        
        if student_response.status_code == 200:
            # Extract student data from API response
            student_api_output = student_response.json().get('data', {})
            
            # Set student data in session
            request.session['student_data'] = student_api_output
            
            # Print student data stored in session
            # print("Student data stored in session:", student_api_output)
            
            # Filter student data based on selected admin numbers
            matching_students = [student_data for student_data in student_api_output.values() if student_data.get('adminno') in selected_admin_numbers]
            
            # Get the first name and last name of the first student (assuming only one student is selected)
            first_name = matching_students[0].get('firstname', '') if matching_students else ''
            last_name = matching_students[0].get('lastname', '') if matching_students else ''
                
        else:
            print("Failed to fetch student data from the API")
            first_name = ''
            last_name = ''
            
    except requests.exceptions.RequestException as e:
        print(f'Error: {e}')
        first_name = ''
        last_name = ''
        
    # API endpoint URL for notification counts
    notification_api_url = 'https://mispack.in/app/admin/public/getmessagecount'
    
    # API parameters for notification counts
    notification_api_data = {
        "contact": mobile_number,
        "adminno": selected_admin_numbers[0] if selected_admin_numbers else None  # Assuming only one admin number is selected
    }
    
    try:
        # Make API request for notification counts with SSL verification disabled
        notification_response = requests.post(notification_api_url, json=notification_api_data, verify=False)
        
        if notification_response.status_code == 200:
            notification_output = notification_response.json()
            if isinstance(notification_output['response'], list) and len(notification_output['response']) > 0:
                notification_counts = notification_output['response'][0]
            else:
                notification_counts = None
        else:
            notification_counts = None
    except requests.exceptions.RequestException as e:
        notification_counts = None
    
    return render(request, 'city_school/dashboard.html', {'first_name': first_name, 'last_name': last_name, 'notification_counts': notification_counts})


##################################### Pending Acceptance ##################################################################

def Pending_acceptance(request):
    return render(request,'city_school/pending_acceptance.html')

##################################### My Student Page ##################################################################

def My_students(request):
    if request.method == 'GET':
        # Assuming you have the mobile number stored in session
        mobile_number = request.session.get('mobile_number')
        if mobile_number:
            # Make a POST request to the API
            api_url = 'https://mispack.in/app/admin/public/getAllStudent'
            data = {'mobile': mobile_number}
            try:
                response = requests.post(api_url, json=data, verify=False)  # Bypass SSL verification

                # Check if the request was successful
                if response.status_code == 200:
                    # Extract data from the API response
                    api_data = response.json()
                    students = api_data.get('data', {}).values()  # Get the list of students
                    
                    # print(students)

                    # Pass the student data to the template for rendering
                    return render(request, 'city_school/my_student.html', {'students': students})
                else:
                    # Handle API request failure
                    return render(request, 'error.html', {'message': 'Failed to fetch student data from the API'})
            except requests.exceptions.RequestException as e:
                # Handle connection or request errors
                return render(request, 'error.html', {'message': f'Error: {e}'})
        else:
            # Handle missing mobile number in session
            return render(request, 'error.html', {'message': 'Mobile number not found in session'})
    else:
        # Handle unsupported HTTP method
        return render(request, 'error.html', {'message': 'Unsupported HTTP method'})
    

##################################### Store Admin No ##################################################################

def store_admin_number(request):
    if request.method == 'POST':
        admin_numbers = request.POST.getlist('admin_numbers[]')
        if admin_numbers:
            request.session['selected_admin_numbers'] = admin_numbers
            
            # Printing session data for verification
            # print("Session data:", request.session['selected_admin_numbers'])

            # Redirect to the profile page after successful selection
            return redirect('dashboard')  # Assuming 'profile' is the URL name for the profile page
        else:
            return render(request, 'error.html', {'message': 'Admin numbers not found in the request'})
    else:
        return render(request, 'error.html', {'message': 'Unsupported HTTP method'})

##################################### Profile Page ##################################################################
from django.conf import settings
import os
# def Profile(request):
#     # Retrieve the selected admin numbers from the session
#     selected_admin_numbers = request.session.get('selected_admin_numbers', [])

#     # Retrieve the mobile number from the session
#     mobile_number = request.session.get('mobile_number')

#     # Make a request to the API to get all students
#     api_url = 'https://mispack.in/app/admin/public/getAllStudent'
#     data = {'mobile': mobile_number}
    
#     try:
#         response = requests.post(api_url, json=data, verify=False)  # Bypass SSL verification

#         # Check if the request was successful
#         if response.status_code == 200:
#             # Extract data from the API response
#             api_data = response.json().get('data', {})
            
#             # Filter the data based on selected_admin_numbers
#             matching_students = [student_data for student_data in api_data.values() if student_data.get('adminno') in selected_admin_numbers]
            
#             # Remove duplicate entries
#             matching_students = list({student['adminno']: student for student in matching_students}.values())

#             # Generate barcode for each student
#             for student in matching_students:
#                 barcode_number = student.get('barcode', '')  # Assuming barcode number is stored in the 'barcode' field
#                 code128 = Code128(barcode_number, writer=ImageWriter())
#                 temp_file = code128.save(os.path.join(settings.STATIC_IMG_ROOT,'assets', 'img', 'temp_barcode'))
#                 # print(temp_file)
#                 with open(temp_file, 'rb') as f:
#                     barcode_image_data = f.read()
#                     barcode_image_base64 = base64.b64encode(barcode_image_data).decode('utf-8')
#                 student['barcode_image'] = barcode_image_base64
                
#             # Store the API data in the session
#             request.session['api_data'] = json.dumps(matching_students)

#             # Pass the matching student data to the template for rendering
#             return render(request, 'city_school/profile.html', {'selected_admin_numbers': selected_admin_numbers, 'matching_students': matching_students})
#         else:
#             # Handle API request failure
#             return render(request, 'error.html', {'message': 'Failed to fetch student data from the API'})
#     except requests.exceptions.RequestException as e:
#         # Handle connection or request errors
#         return render(request, 'error.html', {'message': f'Error: {e}'})

def Profile(request):
    # Retrieve the selected admin numbers from the session
    selected_admin_numbers = request.session.get('selected_admin_numbers', [])

    # Retrieve the mobile number from the session
    mobile_number = request.session.get('mobile_number')

    # Make a request to the API to get all students
    api_url = 'https://mispack.in/app/admin/public/getAllStudent'
    data = {'mobile': mobile_number}
    
    try:
        response = requests.post(api_url, json=data, verify=False)  # Bypass SSL verification

        # Check if the request was successful
        if response.status_code == 200:
            # Extract data from the API response
            api_data = response.json().get('data', {})
            
            # Filter the data based on selected_admin_numbers
            matching_students = [student_data for student_data in api_data.values() if student_data.get('adminno') in selected_admin_numbers]
            
            # Remove duplicate entries
            matching_students = list({student['adminno']: student for student in matching_students}.values())

            # Pass the matching student data to the template for rendering
            return render(request, 'city_school/profile.html', {'selected_admin_numbers': selected_admin_numbers, 'matching_students': matching_students})
        else:
            # Handle API request failure
            return render(request, 'error.html', {'message': 'Failed to fetch student data from the API'})
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})

##################################### Attendence Page ##################################################################


# def Attendance(request):
#     # Retrieve student data from session
#     student_data = request.session.get('student_data', {})
   
#     # print(student_data)
    
#     # Extract mobile number and adminno
#     mobile_number = ''
#     adminno = ''
#     for key, data in student_data.items():
#         mobile_number = data.get('contact', '')
#         adminno = data.get('adminno', '')
#         if mobile_number and adminno:
#             break  # Stop looping if both mobile number and adminno are found

#     # API parameters for circulars
#     api_params_circulars = {
#         "custid": student_data['1']['custid'],
#         "grno": student_data['1']['grnno'],
#         "type": "ATTENDANCE",
#         "classid": student_data['1']['classid'],
#         "divid": student_data['1']['division'],
#         "access": "Parent",
#         "mobile": mobile_number
#     }
    
#     # API endpoint for circulars
#     api_url_circulars = "https://mispack.in/app/admin/public/gettype"

#     try:
#         # Make a POST request to fetch circulars data with SSL verification bypassed
#         response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

#         # Check if the request was successful (status code 200)
#         if response_circulars.status_code == 200:
#             # Parse the JSON response for circulars
#             data_circulars = response_circulars.json()

#             # Extract circulars from the response
#             circulars = [{
#                 "type": circular['type'],
#                 'date': circular['date'],
#                 'description': circular['description'],
#                 'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
#             } for circular in data_circulars.get('response', [])]

#             # Prepare the context to pass to the template
#             context = {'circulars': circulars}

#             # Send POST request to update message count API
#             api_params_update_message_count = {
#                 "type": "ATTENDANCE",
#                 "contact": mobile_number,
#                 "adminno": adminno
#             }
        
#             api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
#             # Make a POST request to update message count with SSL verification bypassed
#             requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

#             # Render the template with the context
#             return render(request, 'city_school/attendance.html', context)
#         else:
#             # Handle errors, for example, by returning an error page
#             return HttpResponse("Error occurred while fetching data from the API")
#     except requests.exceptions.RequestException as e:
#         # Handle connection or request errors
#         return render(request, 'error.html', {'message': f'Error: {e}'})


def Attendance(request):
    try:
        # Retrieve student data from session
        student_data = request.session.get('student_data', {})
       
        # Extract mobile number and adminno
        mobile_number = ''
        adminno = ''
        for key, data in student_data.items():
            mobile_number = data.get('contact', '')
            adminno = data.get('adminno', '')
            if mobile_number and adminno:
                break  # Stop looping if both mobile number and adminno are found

        # API parameters for circulars
        api_params_circulars = {
            "custid": student_data['1']['custid'],
            "grno": student_data['1']['grnno'],
            "type": "ATTENDANCE",
            "classid": student_data['1']['classid'],
            "divid": student_data['1']['division'],
            "access": "Parent",
            "mobile": mobile_number
        }
        
        # API endpoint for circulars
        api_url_circulars = "https://mispack.in/app/admin/public/gettype"

        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)
        
        # print(response_circulars.json().get('response'))

        # Check if the request was successful (status code 200)
        if response_circulars.json().get('response'):
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "type": circular['type'],
                'date': circular['date'],
                'description': circular['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
            } for circular in data_circulars.get('response', [])]

            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "ATTENDANCE",
                "contact": mobile_number,
                "adminno": adminno
            }
        
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/attendance.html', context)
        else:
            # Handle errors, for example, by returning an error page
            # return HttpResponse("Error occurred while fetching data from the API")
            messages.success(request, "NO DATA FOUND")
            return render(request, 'city_school/attendance.html')
        
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})




##################################### Circular Page ##################################################################

def Circular(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
   
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "CIRCULAR",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    # print(api_params_circulars)
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # # Extract circulars from the response
            # circulars = [{
            #     "type": circular['type'],
            #     'date': circular['date'],
            #     'description': circular['description'],
            #     'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
            # } for circular in data_circulars.get('response', [])]
            
            # Extract circulars from the response
            circulars = [{
                "type": data_circulars['response'][key]['type'],
                'date': data_circulars['response'][key]['date'],
                'description': data_circulars['response'][key]['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{data_circulars['response'][key]['uid']}"
            } for key in data_circulars.get('response', {}).keys()]


            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "CIRCULAR",
                "contact": mobile_number,
                "adminno": adminno
            }
           
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/circular.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})

##################################### Assigment page ##################################################################


def Assignment(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
   
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "CIRCULAR",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "type": data_circulars['response'][key]['type'],
                'date': data_circulars['response'][key]['date'],
                'description': data_circulars['response'][key]['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{data_circulars['response'][key]['uid']}"
            } for key in data_circulars.get('response', {}).keys()]


            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "ATTENDANCE",
                "contact": mobile_number,
                "adminno": adminno
            }
            # print(api_params_update_message_count)
            
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/assignment.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})


##################################### Event Page ##################################################################

# def Event(request):
#      # Sample dynamic data
#     api_data = json.loads(request.session.get('api_data', '[]'))

#     if api_data:
#         # Extract necessary fields from api_data
#         custid = api_data[0].get('custid', '')
#         grno = api_data[0].get('grno', '')
#         classid = api_data[0].get('classid', '')
#         divid = api_data[0].get('divid', '')
#         access = api_data[0].get('access', '')
#         mobile_number = api_data[0].get('mobile', '')

#         # Update the payload with the retrieved values
#         payload = {
#             "custid": custid,
#             "grno": grno,
#             "type": "EVENTS",
#             "classid": classid,
#             "divid": divid,
#             "access": access,
#             "mobile": mobile_number
#         }

#         # API endpoint
#         api_url = "https://mispack.in/app/admin/public/gettype"

#         try:
#             # Make a POST request to the API with SSL verification bypassed
#             response = requests.post(api_url, json=payload, verify=False)

#             # Check if the request was successful (status code 200)
#             if response.status_code == 200:
#                 # Parse the JSON response
#                 data = response.json()

#                # Extract assignments from the response
#                 circulars = [{
#                     "id":circular['id'],
#                     "type": circular['type'],
#                     'date': circular['date'],
#                     'description': circular['description'],
#                     'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"  # Adjust the link format as per your requirement
#                 } for circular in data.get('response', [])]

#                 # Prepare the context to pass to the template
#                 context = {'circulars': circulars, 'api_data': api_data}

#                 # Render the template with the context
#                 return render(request,'city_school/event.html', context)
#             else:
#                 # Handle errors, for example, by returning an error page
#                 return HttpResponse("Error occurred while fetching data from the API")
#         except requests.exceptions.RequestException as e:
#             # Handle connection or request errors
#             return render(request, 'error.html', {'message': f'Error: {e}'})
#     else:
#         # Handle the case when api_data is empty
#         return render(request, 'error.html', {'message': 'API data not found in session'})
    
def Event(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
   
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "EVENTS",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "id":circular['id'],
                "type": circular['type'],
                'date': circular['date'],
                'description': circular['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
            } for circular in data_circulars.get('response', [])]

            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "EVENTS",
                "contact": mobile_number,
                "adminno": adminno
            }
           
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/event.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})


##################################### Examination Page ##################################################################

def Examination(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
   
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "CIRCULAR",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "type": data_circulars['response'][key]['type'],
                'date': data_circulars['response'][key]['date'],
                'description': data_circulars['response'][key]['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{data_circulars['response'][key]['uid']}"
            } for key in data_circulars.get('response', {}).keys()]


            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "EXAMINATION",
                "contact": mobile_number,
                "adminno": adminno
            }
           
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/examination.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})

##################################### Fees Page ##################################################################

def Fees(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
    
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "FEES",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "type": circular['type'],
                'date': circular['date'],
                'description': circular['description'],
                # 'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
            } for circular in data_circulars.get('response', [])]

            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "FEES",
                "contact": mobile_number,
                "adminno": adminno
            }
            
            # print(api_params_update_message_count)
            
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/fees.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})

##################################### Media Page ##################################################################

def Media(request):
    # Retrieve student data from session
    student_data = request.session.get('student_data', {})
    
    # Extract mobile number and adminno
    mobile_number = ''
    adminno = ''
    for key, data in student_data.items():
        mobile_number = data.get('contact', '')
        adminno = data.get('adminno', '')
        if mobile_number and adminno:
            break  # Stop looping if both mobile number and adminno are found

    # API parameters for circulars
    api_params_circulars = {
        "custid": student_data['1']['custid'],
        "grno": student_data['1']['grnno'],
        "type": "PAYROLL",
        "classid": student_data['1']['classid'],
        "divid": student_data['1']['division'],
        "access": "Parent",
        "mobile": mobile_number
    }
    
    # API endpoint for circulars
    api_url_circulars = "https://mispack.in/app/admin/public/gettype"

    try:
        # Make a POST request to fetch circulars data with SSL verification bypassed
        response_circulars = requests.post(api_url_circulars, json=api_params_circulars, verify=False)

        # Check if the request was successful (status code 200)
        if response_circulars.status_code == 200:
            # Parse the JSON response for circulars
            data_circulars = response_circulars.json()

            # Extract circulars from the response
            circulars = [{
                "type": circular['type'],
                'date': circular['date'],
                'description': circular['description'],
                'pdf_link': f"https://www.mispack.in/app/application/main/{circular['uid']}"
            } for circular in data_circulars.get('response', [])]

            # Prepare the context to pass to the template
            context = {'circulars': circulars}

            # Send POST request to update message count API
            api_params_update_message_count = {
                "type": "PAYROLL",
                "contact": mobile_number,
                "adminno": adminno
            }
            
            
            api_url_update_message_count = "https://mispack.in/app/admin/public/updatemessagecount"
            
            # Make a POST request to update message count with SSL verification bypassed
            requests.post(api_url_update_message_count, json=api_params_update_message_count, verify=False)

            # Render the template with the context
            return render(request, 'city_school/media.html', context)
        else:
            # Handle errors, for example, by returning an error page
            return HttpResponse("Error occurred while fetching data from the API")
    except requests.exceptions.RequestException as e:
        # Handle connection or request errors
        return render(request, 'error.html', {'message': f'Error: {e}'})

##################################### PDF Page ##################################################################

def Pdf(request):
    pdf_link = request.GET.get('pdf_link', '')  # Get the PDF link from the query parameters
    description = request.GET.get('description', '')  # Get the description from the query parameters
    circular_type = request.GET.get('type', '')  # Get the type from the query parameters
    return render(request, 'city_school/pdf.html', {'pdf_link': pdf_link, 'description': description, 'type': circular_type})


##################################### Photo Page ##################################################################

# Suppress SSL warnings
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
def Photo(request, circular_id):
    # print("Received Circular ID:", circular_id)
    
    # API endpoint for fetching post details
    post_api_url = "https://mispack.in/app/admin/public/getpost"
    # Parameters for the API request
    payload = {"id": circular_id}

    # Make GET request to the API with SSL certificate verification disabled
    response = requests.post(post_api_url, json=payload, verify=False)
    
    # print(response.json())
    
    # Print the response content
    # print("Response Content:", response.content)

    # Extract image URLs and description from the response
    try:
        data = response.json()
        if 'response' in data and data['response']:
            post = data['response'][0]
            description = post.get('description', '')  # Get description from API response
            image_urls = []
            for image_array in post.get('image_array', []):
                image_url = f"https://www.mispack.in/app/application/main/{image_array['image']}"
                image_urls.append(image_url)
            # print(image_urls)
        else:
            # Handle the case when there's no response or no images found
            description = ''  # If no response or description is found, set to empty string
            image_urls = []
    except Exception as e:  
        print("Failed to decode JSON:", e)
        description = ''  # Set description to empty string in case of exception
        image_urls = []

    # Render the template with the retrieved image URLs and description
    return render(request, 'city_school/photo.html', {'image_urls': image_urls, 'description': description, 'circular_id': circular_id})



##################################### Imagespecific Page ##################################################################

from django.shortcuts import render

def Imagespecific(request):
    # Get the image URL from the query parameters
    image_url = request.GET.get('image_url', None)
    circular_id = request.GET.get('circular_id', None)
    return render(request, 'city_school/imagespecific.html', {'image_url': image_url, 'circular_id': circular_id})

##################################### Imagespecific Page ##################################################################
def Logout(request):
    # Clear all sessions
    request.session.clear()
    # Redirect to the login page
    return redirect('login')