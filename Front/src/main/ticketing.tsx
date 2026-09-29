import { Platform, View } from "react-native";
import WebView from "react-native-webview";



const Ticketing = () => {
    const url = `https://ticketing.rodanai.com.ar/login.html`;
    return (
        <View className="flex w-full">
          {Platform.OS === "web" ? (
            <iframe
              src={url}
              className="w-full h-screen border-none"
              title="NetSuite Login"
            />
          ) : (
            <WebView source={{ uri: url }} style={{ flex: 1 }} />
          )}
        </View>
    );
}

export default Ticketing;