import React from 'react';
import { Component } from '../widgets/components';

const GlobalPermissions:React.FC<{session:(value:boolean)=>void}> = ({session}) => {
    const endpoint = '/global_permissions'
    const title = 'Global Permissions'
    return (
        <Component title={title} endpoint={endpoint} session={session} />
    );
};

export default GlobalPermissions;