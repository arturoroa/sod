import React from 'react';
import { ScrollView, View } from 'react-native';
import { Body, Header } from '../widgets/components';

const Relationships:React.FC<{session:(value:boolean)=>void}> = ({session}) => {
    const title = 'Relationships'
    const endpoints = ['/role_permissions', '/employee_roles', '/role_subsidiaries']

    return (
        <View className="flex flex-col min-h-screen h-screen bg-gray-100 font-sans min-w-[320px] w-full overflow-hidden">
            <Header title={title}></Header>
            <View className='flex-1 min-h-0 p-4 space-y-6 overflow-hidden'>
                {endpoints.map((endpoint, index)=>(
                    <View key={index} className='flex-none h-[calc((100vh-180px)/3)] min-h-0 w-full overflow-hidden'>
                        <Body endpoint={endpoint} session={session} fullHeight={false} />
                    </View>
                ))}
            </View>
        </View>
    );
};

export default Relationships;