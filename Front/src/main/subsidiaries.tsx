import React from 'react';
import { Component } from '../widgets/components';

const Subsidiaries:React.FC<{session:(value:boolean)=>void}> = ({session}) => {
    const endpoint = '/subsidiaries'
    const title = 'Subsidiaries'
    return (
        <Component title={title} endpoint={endpoint} session={session}/>
    );
};

export default Subsidiaries;