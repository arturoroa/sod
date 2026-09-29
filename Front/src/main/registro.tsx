import React, { useState } from 'react';
import { View, Text, ScrollView, TextInput, TouchableOpacity } from 'react-native';
import { Picker } from '@react-native-picker/picker';
import {Eye as LView, EyeClosed} from 'lucide-react-native';
import { getData } from '../services/storage';
import { upload } from '../services/generalService';
import { RenderWebView } from '../widgets/webviews';
import { UploadFile } from '../widgets/uploadFile';

const Registro = () => {
  const [refreshKey, setRefreshKey] = useState(0);
  const [selectedValue, setSelectedValue] = useState('java');
  const [passwordVisible, setPasswordVisible] = useState(false);

  const refresh = () => {
    setRefreshKey((refreshKey) => refreshKey + 1);
  };

  return (
    <View className="flex flex-col min-h-screen bg-gray-100 font-sans w-full">
      {/* Header */}
      <View className="flex items-center justify-center h-[110px] bg-gradient-to-r from-[#0d1b2a] via-[#13263c] to-[#0b1724] border-b border-white/10 shadow-[0_20px_60px_rgba(4,20,32,0.45)]">
        <Text className="text-center text-white tracking-[0.12em] font-extrabold text-4xl uppercase">Registry</Text>
      </View>
      <View className="flex-1 p-6 space-y-8">
        {/* Form Section */}
        <View className="bg-white border border-gray-200 rounded-lg shadow-lg">
          <Text className="text-xl font-semibold bg-slate-500 text-white py-4 rounded-t-lg text-center">
            Database
          </Text>
          <View className="p-6">
            <ScrollView className="w-full space-y-6">
              <TextInput
                placeholder="UserID"
                className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800 mb-4"
                placeholderTextColor="gray"
              />
              <View className="relative w-full justify-center items-center align-middle">
                <TextInput
                  placeholder="Password"
                  secureTextEntry={!passwordVisible}
                  className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800  mb-4"
                  placeholderTextColor="gray"
                />
                <TouchableOpacity
                  className="absolute right-4 top-3"
                  onPress={() => setPasswordVisible(!passwordVisible)}
                >
                  <Text className="text-blue-500 font-semibold">
                    {passwordVisible ?  <LView color="black" />: <EyeClosed color="black" /> }
                  </Text>
                </TouchableOpacity>
              </View>
              <Picker
                selectedValue={selectedValue}
                onValueChange={(itemValue) => setSelectedValue(itemValue)}
                className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800  mb-4"
              >
                <Picker.Item label="0" value="0" />
                <Picker.Item label="1" value="1" />
                <Picker.Item label="2" value="2" />
              </Picker>
              <TextInput
                placeholder="Company"
                className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800  mb-4"
                placeholderTextColor="gray"
              />
              <TextInput
                placeholder="Email"
                className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800 mb-4"
                placeholderTextColor="gray"
              />
              <TextInput
                placeholder="Phone"
                className="border border-gray-300 rounded-lg px-4 py-3 w-full text-gray-800 "
                placeholderTextColor="gray"
              />

              <TouchableOpacity
                className="flex w-24  items-center justify-center bg-blue-500 px-4 py-2 rounded-lg text-white mt-4"
                onPress={refresh}
              >
                <Text className="text-white">Refresh</Text>
              </TouchableOpacity>
            </ScrollView>
          </View>
        </View>
      </View>
    </View>
  );
};

export default Registro;
