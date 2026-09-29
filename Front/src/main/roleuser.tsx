import React, { useState } from 'react';
import { View, Text, ScrollView} from 'react-native';
import { RenderWebView } from '../widgets/webviews';
import { UploadFile } from '../widgets/uploadFile';

const RoleuserComponent = () => {
  const [refreshKey, setRefreshKey] = useState(0);

  const refresh = () => {
    setRefreshKey((refreshKey) => refreshKey + 1);
  };

  return (
    <View className="flex flex-col min-h-screen bg-gray-100 font-sans w-full">
      {/* Header */}
      <View className="flex items-center justify-center h-[110px] bg-gradient-to-r from-[#0d1b2a] via-[#13263c] to-[#0b1724] border-b border-white/10 shadow-[0_20px_60px_rgba(4,20,32,0.45)]">
        <Text className="text-center text-white tracking-[0.12em] font-extrabold text-4xl uppercase">Users</Text>
      </View>
      {/* /upload_user */}
      <View className="flex-1 p-6 space-y-8">
        {/*<UploadFile endpoint='/upload_user' refresh={refresh}/>*/}

        <View className="bg-white border border-gray-200 rounded-lg shadow-lg">
        <Text className="text-xl font-semibold bg-slate-500 text-white py-4 rounded-t-lg text-center">
            Role to User Data
          </Text>
        <View className="p-6 ">
            <View className="h-[500px] w-full  rounded overflow-hidden">
              {/* /get_user_html 
              <Text  className="text-center text-gray-500">[Users Table Placeholder]</Text>*/}
              <ScrollView className="w-full" contentContainerStyle={{ flexGrow: 1 }}>
              <RenderWebView key={refreshKey} endpoint='/get_user_html' option={false}/>
              </ScrollView>
            </View>
          </View>
        </View>
      </View>
    </View>
  );
};

export default RoleuserComponent;