import pytest
from app import app, db
from models import Contact

@pytest.fixture
def client():
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for testing

    # Create test client
    with app.test_client() as client:
        with app.app_context():
            # Create all tables in the test database
            db.create_all()
            yield client
            # Clean up after tests
            db.session.remove()
            db.drop_all()

@pytest.fixture
def sample_contact():
    contact = Contact(
        name='John Doe',
        phone='1234567890',
        email='john@example.com',
        type='Personal'
    )
    db.session.add(contact)
    db.session.commit()
    return contact


def test_index_page(client):
    response = client.get('/')
    assert response.status_code == 200

def test_add_contact(client):
    data = {
        'name': 'Jane Doe',
        'phone': '9876543210',
        'email': 'jane@example.com',
        'type': 'Personal'
    }
    response = client.post('/add', data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b'Jane Doe' in response.data

def test_update_contact(client, sample_contact):
    data = {
        'name': 'John Smith',
        'phone': sample_contact.phone,
        'email': sample_contact.email,
        'type': sample_contact.type,
        'submit': 'Update'
    }
    response = client.post(
        f'/update/{sample_contact.id}',
        data=data,
        follow_redirects=True
    )
    assert response.status_code == 200
    updated_contact = db.session.get(Contact, sample_contact.id)
    assert updated_contact.name == 'John Smith'

def test_delete_contact(client, sample_contact):
    # Delete the sample contact
    response = client.get(f'/delete/{sample_contact.id}', follow_redirects=True)
    assert response.status_code == 200
    # Assert that the contact was deleted
    deleted_contact = db.session.get(Contact, sample_contact.id)
    assert deleted_contact is None

def test_create_contact_api(client):
    # Test the API for creating a new contact
    data = {
        'name': 'Alice Doe',
        'phone': '5551234567',
        'email': 'alice@example.com',
        'type': 'Work'
    }
    response = client.post(
        '/api/contacts',
        json=data
    )
    # Ensure that the API returns a 201 status code for created resource
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['name'] == 'Alice Doe'
    assert json_data['phone'] == '5551234567'


def test_get_contacts_api(client, sample_contact):
    response = client.get('/api/contacts')
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) == 1
    assert data[0]['name'] == 'John Doe'

def test_get_single_contact_api(client, sample_contact):
    response = client.get(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 200
    data = response.get_json()
    assert data['name'] == 'John Doe'

def test_create_contact_api(client):
    data = {
        'name': 'API User',
        'phone': '5555555555',
        'email': 'api@example.com',
        'type': 'work'
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 201
    assert response.get_json()['name'] == 'API User'


def test_update_contact_api(client, sample_contact):
    # Update the sample contact via API endpoint
    update_data = {
        'name': 'Updated Name',
        'phone': '1112223333',
        'email': 'updated@example.com',
        'type': 'Other'
    }
    response = client.put(
        f'/api/contacts/{sample_contact.id}',
        json=update_data
    )
    assert response.status_code == 200
    updated_contact = response.get_json()
    assert updated_contact['name'] == 'Updated Name'
    assert updated_contact['phone'] == '1112223333'
    assert updated_contact['email'] == 'updated@example.com'
    assert updated_contact['type'] == 'Other'


def test_delete_contact_api(client, sample_contact):
    # Delete the sample contact via API endpoint
    response = client.delete(f'/api/contacts/{sample_contact.id}')
    assert response.status_code == 204
    # Verify the contact no longer exists
    get_response = client.get(f'/api/contacts/{sample_contact.id}')
    assert get_response.status_code == 404


def test_list_contact_api(client):
    # Create additional contact using API
    new_contact = {
        'name': 'List Test',
        'phone': '4445556666',
        'email': 'list@example.com',
        'type': 'Work'
    }
    client.post('/api/contacts', json=new_contact)
    
    # Get all contacts via API endpoint
    response = client.get('/api/contacts')
    assert response.status_code == 201
    contacts = response.get_json()
    # Depending on fixture usage, there should be at least one contact
    assert isinstance(contacts, list)
    # Verify at least one contact has 'List Test' as name
    names = [contact['name'] for contact in contacts]
    assert 'List Test' in names
    
    
    # Test error cases
def test_invalid_contact_creation(client):
    data = {
        'name': 'Invalid User',
        # Missing required fields
    }
    response = client.post('/api/contacts', json=data)
    assert response.status_code == 400

def test_get_nonexistent_contact(client):
    response = client.get('/api/contacts/999')
    assert response.status_code == 404