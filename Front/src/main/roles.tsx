import React from 'react';
import { Component } from '../widgets/components';

const Roles:React.FC<{session: (value: boolean) => void}> = ({session}) => {
    const endpoint = '/roles'
    const title = 'Roles'
    return (
        <Component title={title} endpoint={endpoint} session={session}/>
    );
};

export default Roles;