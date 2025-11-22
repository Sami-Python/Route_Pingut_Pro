from configparser import SectionProxy
from azure.identity import DeviceCodeCredential, TokenCachePersistenceOptions
from msgraph import GraphServiceClient
from msgraph.generated.users.item.user_item_request_builder import UserItemRequestBuilder
from msgraph.generated.users.item.mail_folders.item.messages.messages_request_builder import (
    MessagesRequestBuilder)
from msgraph.generated.users.item.send_mail.send_mail_post_request_body import (
    SendMailPostRequestBody)
from msgraph.generated.models.message import Message
from msgraph.generated.models.item_body import ItemBody
from msgraph.generated.models.body_type import BodyType
from msgraph.generated.models.recipient import Recipient
from msgraph.generated.models.email_address import EmailAddress

class Graph:
    settings: SectionProxy
    device_code_credential: DeviceCodeCredential
    user_client: GraphServiceClient

    def __init__(self, config: SectionProxy):
        self.settings = config
        client_id = self.settings['clientId']
        tenant_id = self.settings['tenantId']
        graph_scopes = self.settings['graphUserScopes'].split(' ')

        # Configure persistent token caching
        # This will create a file in your home directory to store the refresh token
        cache_options = TokenCachePersistenceOptions(name="graph_token_cache",allow_unencrypted_storage=True)

        self.device_code_credential = DeviceCodeCredential(
            client_id,
            tenant_id=tenant_id,
            cache_persistence_options=cache_options
        )
        self.user_client = GraphServiceClient(self.device_code_credential, graph_scopes)

    def get_user_token(self):
        graph_scopes = self.settings['graphUserScopes'].split(' ')
        # The credential will now automatically use the cache.
        # If a valid token is in the cache, it will be returned.
        # If the token is expired but a refresh token is available, it will be used to get a new one.
        # If no valid token or refresh token is in the cache, it will fall back to the device code flow.
        access_token = self.device_code_credential.get_token(*graph_scopes)
        return access_token.token
    
    async def get_user(self):
        # Only request specific properties using $select
        query_params = UserItemRequestBuilder.UserItemRequestBuilderGetQueryParameters(
            select=['displayName', 'mail', 'userPrincipalName']
        )

        request_config = UserItemRequestBuilder.UserItemRequestBuilderGetRequestConfiguration(
            query_parameters=query_params
        )

        user = await self.user_client.me.get(request_configuration=request_config)
        return user
    
    async def get_inbox(self):
        query_params = MessagesRequestBuilder.MessagesRequestBuilderGetQueryParameters(
            # Only request specific properties
            select=['from', 'isRead', 'receivedDateTime', 'subject'],
            # Get at most 25 results
            top=25,
            # Sort by received time, newest first
            orderby=['receivedDateTime DESC']
        )
        request_config = MessagesRequestBuilder.MessagesRequestBuilderGetRequestConfiguration(
            query_parameters= query_params
        )
    
        messages = await self.user_client.me.mail_folders.by_mail_folder_id('inbox').messages.get(
                request_configuration=request_config)
        return messages