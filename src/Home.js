import React, { useEffect, useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet, Image, ActivityIndicator, Linking } from 'react-native';
import { GiftedChat, Send, Bubble } from 'react-native-gifted-chat';
import Icon from 'react-native-vector-icons/AntDesign';
import MaterialIcons from 'react-native-vector-icons/MaterialIcons';
import DocumentPicker from 'react-native-document-picker';
import { scale } from 'react-native-size-matters';
import { API_KEY, API_TOKEN, API_URL_UPLOAD, API_URL_ASK } from '../constant';


const ChatScreen = () => {
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [inputText, setInputText] = useState(''); // Manage input field state
  const [uploadStatus, setUploadStatus] = useState(null); // New state for upload status
  useEffect(() => {
    // Send a welcome message from the bot when the component mounts
    const welcomeMessage = {
      _id: new Date().getTime(),
      text: `Welcome to SpendWise! 🎉\n\n` +
        `I’m here to help you understand your spending patterns with ease. Simply upload your bank statement, and I’ll categorize your transactions into the following categories:\n` +
        `- Fitness\n` +
        `- Groceries\n` +
        `- Restaurants and Cafes\n` +
        `- Healthcare\n` +
        `- Clothing\n` +
        `- Jewelry\n` +
        `- Transportation\n` +
        `- Phone and Internet\n` +
        `- Miscellaneous\n` +
        `- Others\n` +
        `- E-commerce\n` +
        `- Food Delivery\n\n` +
        `Currently, I support statements from NBD Bank. If you want to give me a try, I already have a sample data loaded for you.`,
      user: { _id: 2 }, // Bot user ID
    };
    setMessages([welcomeMessage]); // Set initial messages including the welcome message
  }, []);

  useEffect(() => {
    if (uploadStatus === 'success') {
      const timer = setTimeout(() => {
        setUploadStatus(null); // Hide tick icon after 3 seconds
      }, 2000);

      return () => clearTimeout(timer); // Cleanup timeout on component unmount
    }
  }, [uploadStatus]);
  const onSend = async (newMessages = []) => {
    // Add the new message to the chat
    setMessages((previousMessages) =>
      GiftedChat.append(previousMessages, newMessages)
    );

    // Handle user message
    if (newMessages.length > 0) {
      const message = newMessages[0];
      if (message.text) {
        handleQuery(message.text);
        setInputText(''); // Clear input field
      }
    }
  };

  const handleDocumentPicker = async () => {
    try {
      const res = await DocumentPicker.pick({
        type: [DocumentPicker.types.pdf],
      });

      console.log('DocumentPicker result:', res);

      if (res && res.length > 0) {
        const file = res[0];

        setLoading(true);
        setUploadStatus(null); // Reset upload status

        const formData = new FormData();
        formData.append('file', {
          uri: file.uri,
          type: 'application/pdf',
          name: file.name,
        });

        console.log('Uploading file:', file.uri);
        const response = await fetch(API_URL_UPLOAD, {
          method: 'POST',
          headers: {
            'X-Token': API_KEY,
            'Authorization': `Bearer ${API_TOKEN}`,
            'Accept': 'application/json',
          },
          body: formData,
        });

        setLoading(false);

        if (!response.ok) {
          throw new Error(`HTTP error! Status: ${response.status}`);
        }

        const result = await response.json();
        console.log('PDF upload result:', result);

        let pdfMessage;

        if (result.report_content) {
          const reportContent = typeof result.report_content === 'string'
            ? result.report_content
            : (result.report_content || {});

          const fileName = file.name;

          pdfMessage = {
            _id: new Date().getTime(),
            user: { _id: 1 },
          };
          setUploadStatus('success'); // Set upload status to success

        } else {
          console.error('No report_content in response:', result);
          const errorMessage = 'Error: No report content received from the server.';
          pdfMessage = {
            _id: new Date().getTime(),
            text: errorMessage,
            user: { _id: 1 },
          };
          setUploadStatus('error'); // Set upload status to error

        }

        onSend([pdfMessage]);

      } else {
        console.error('No file selected');
      }

    } catch (err) {
      console.error('Error handling document picker:', err);
      setLoading(false);
      setUploadStatus('error'); // Set upload status to error

      const errorMessage = 'An error occurred while uploading the PDF. Please try again.';
      const errorMsg = {
        _id: new Date().getTime(),
        text: errorMessage,
        user: { _id: 1 },
      };
      onSend([errorMsg]);
    }
  };

  const handleQuery = async (query) => {
    try {
      console.log('Sending query to chatbot:', query);

      const response = await fetch(API_URL_ASK, {
        method: 'POST',
        headers: {
          'x-token': API_KEY,
          'Authorization': `Bearer ${API_TOKEN}`,
          'accept': 'application/json',
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: query }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! Status: ${response.status}`);
      }

      const result = await response.json();
      console.log('Chatbot response:', result);

      const { message, response: responseData } = result;

      // Ensure responseData is a string
      const formattedResponse = typeof responseData === 'string'
        ? responseData
        : 'No specific response available.';

      const chatbotMessage = `${formattedResponse}`;

      const queryMessage = {
        _id: new Date().getTime(),
        text: chatbotMessage,
        user: { _id: 2 },
      };

      setMessages((previousMessages) =>
        GiftedChat.append(previousMessages, [queryMessage])
      );
    } catch (err) {
      console.error('Error handling query:', err);
      const errorMessage = 'There was an error processing your query. Please try again.';

      const queryMessage = {
        _id: new Date().getTime(),
        text: errorMessage,
        user: { _id: 2 },
      };

      setMessages((previousMessages) =>
        GiftedChat.append(previousMessages, [queryMessage])
      );
    }
  };




  const renderSend = (props) => (
    <Send {...props}>
      <View style={styles.sendButtonContainer}>
        <TouchableOpacity onPress={handleDocumentPicker}>
          <View style={styles.iconButton}>
            <MaterialIcons name="attach-file" size={16} color="#fff" />
          </View>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => {
          if (inputText.trim()) {
            props.onSend({ text: inputText });
            setInputText(''); // Clear input field
          }
        }}>
          <View style={styles.sendButton}>
            <Icon name="arrowright" size={16} color="#fff" />
          </View>
        </TouchableOpacity>
      </View>
    </Send>
  );




  const renderMessage = (props) => {
    const { currentMessage } = props;

    // Define custom styles for user messages
    const userMessageStyle = {
      backgroundColor: '#495D87', // Replace with desired color for user messages
      borderRadius: scale(10), // Adjust border radius as needed
      marginBottom: scale(10),
    };

    // Define custom styles for bot messages
    const botMessageStyle = {
      backgroundColor: '#F0F0F0', // Replace with desired color for bot messages
      borderRadius: scale(10), // Adjust border radius as needed
      marginBottom: scale(10),

    };

    // Apply styles based on user ID
    const messageStyle =
      currentMessage.user._id === 1 ? userMessageStyle : botMessageStyle;

    if (currentMessage.filePath) {
      return (
        <View style={styles.pdfContainer}>
          <MaterialIcons name="attach-file" size={20} color="#000" />
          <TouchableOpacity onPress={() => openFile(currentMessage.filePath)}>
            <Text style={styles.pdfText}>{currentMessage.text}</Text>
          </TouchableOpacity>
        </View>
      );
    }

    return (
      <Bubble
        {...props}
        wrapperStyle={{
          right: { ...messageStyle }, // Apply user message style for the right (current user's) messages
          left: { ...messageStyle },  // Apply bot message style for the left (other user's) messages
        }}
      />
    );
  };


  const openFile = (filePath) => {
    Linking.openURL(filePath);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Image
          source={require('../assets/logo.png')} // Update with your logo path
          style={styles.logo}
        />
        <Text style={styles.headerTitle}>WELCOME TO SPENDWISE</Text>

      </View>
      <GiftedChat
        messages={messages}
        onSend={onSend}
        user={{ _id: 1 }} // User ID for the current user
        renderSend={renderSend}
        renderMessage={renderMessage}
        textInputStyle={styles.textInput} // Apply custom styles to text input
        alwaysShowSend
        textInputProps={{
          value: inputText, // Set the value of the input field
          onChangeText: setInputText, // Update the state when the text changes
        }}
      />
      {loading && (
        <View style={styles.activityIndicatorContainer}>
          <ActivityIndicator size="large" color="#495D87" />
        </View>
      )}
      {uploadStatus === 'success' && (
        <View style={styles.activityIndicatorContainer}>

          <Icon name="checkcircle" size={26} color="#495D87" style={styles.tickIcon} />
        </View>

      )}

    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: "center",
    backgroundColor: '#495D87',
    padding: scale(10),
    paddingVertical: scale(15)
  },
  logo: {
    width: scale(35),
    height: scale(35),
    marginRight: scale(10),
    borderRadius: scale(55)
  },
  headerTitle: {
    color: '#fff',
    fontSize: scale(13),
    fontWeight: 'bold',
    letterSpacing: scale(1.5)
  },
  sendButtonContainer: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  tickIcon: {
    marginLeft: scale(10),
  },
  sendButton: {
    backgroundColor: '#495D87',
    padding: scale(6),
    borderRadius: scale(20),
    marginHorizontal: scale(2),
    marginBottom: scale(10),
    marginRight: scale(5)
  },
  iconButton: {
    backgroundColor: '#495D87',
    padding: scale(6),
    borderRadius: scale(20),
    marginHorizontal: scale(2),
    marginBottom: scale(10)

  },
  textInput: {
    paddingVertical: scale(5),
    paddingHorizontal: scale(10),
    color: '#000', // Set text color to black
  },
  pdfContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: scale(5),
  },
  pdfText: {
    color: '#495D87',
    marginLeft: scale(5),
  },
  activityIndicatorContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    top: 0,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.7)',
    zIndex: 1,
  },
});

export default ChatScreen;